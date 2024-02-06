# __init__()
#   . loaderdb()
#
# upload_loader()
#   . cmd_hello()
#   . get_rsp()
#   . cmd_done()
#   . get_error_desc() doesn't matter that much? 
#
# connect()
#   . cdc.read()
#   . commandhandler()
#     . pkt_cmd_hdr()
#     . pkt_hello_req()
#     . pkt_image_end() ?
#   . cdc.write()
#   . cdc.read()
# 
# cmd_info() - getting the information for the loader
#   . enter_command_mode()
#   . cmdexec_get_msm_hwid()
#   . cmdexec_get_pkhash()
#   . cmd_modeswitch()
#   . cmdexec_get_serial_num()
#     . self.cmd_exec()
# cmd_reset() - Not really important right now
#
# TODO: sahara_defs
import sys
from struct import pack
import time

from loader_db import loader_utils
from qualcomm_config import sochw, msmids, root_cert_hash
from sahara_defs import ErrorDesc, cmd_t, exec_cmd_t, sahara_mode_t, status_t, \
    CommandHandler, SAHARA_VERSION

class sahara:
  def __init__(self, cdc):
    self.cdc = cdc
    self.id = None
    self.programmer = None
    self.mode = ""
    self.version = 2.1
    self.hwid = None
    self.serial = None
    self.serials = None
    self.sblversion = None
    self.pkhash = None
    self.hwidstr = None
    self.ch = CommandHandler()
    self.loader_handler = loader_utils()
    self.loaderdb = self.loader_handler.init_loader_db()

  def connect(self):
    try:
      v = self.cdc.read(length=0xC * 0x4,timeout=1)
      if len(v) > 1:
        if v[0] == 0x01:
          pkt = self.ch.pkt_cmd_hdr(v)
          if pkt.cmd == cmd_t.SAHARA_HELLO_REQ:
            rsp = self.ch.pkt_hello_req(v)
            self.pktsize = rsp.cmd_packet_length
            self.version = rsp.version
            print(f"Protocol version: {rsp.version}, Version supported: {rsp.version_supported}")
            return {"mode":"sahara", "cmd":cmd_t.SAHARA_HELLO_REQ, "data":rsp}
          #elif pkt.cmd == cmd_t.SAHARA_END_TRANSFER:
          #  rsp = self.ch.pkt_image_end(v)
          #  return {"mode":"sahara", "cmd":cmd_t.SAHARA_END_TRANSFER, "data":rsp}
        elif b"<?xml" in v:
          return {"mode":"firehose"}
        elif v[0] == 0x7E:
          return {"mode":"nandprg"}
      else:
        data = b"<?xml version=\"1.0\" ?><data><nop /></data>"
        self.cdc.write(data)
        res = self.cdc.read(timeout=1)
        if b"<?xml" in res:
          return {"mode": "firehose"}
        else:
          print("Only support firehose")
          #elif len(res)> 0:
          #    if res[0] == 0x7E:
          #        return {"mode":"nandprg"}
          #    elif res[0] == cmd_t.SAHARA_END_TRANSFER:
          #        rsp = self.ch.pkt_image_end(res)
          #        return {"mode": "sahara", "cmd": cmd_t.SAHARA_END_TRANSFER, "data": rsp}
          #elif res == b"":
          #    data = b"\x7E\x11\x00\x12\x00\xA0\xE3\x00\x00\xC1\xE5\x01\x40\xA0\xE3\x1E\xFF\x2F\xE1\x4B\xD9\x7E"
          #    self.cdc.write(data)
          #    res = self.cdc.read()
          #    if len(res) > 0 and res[1] == 0x12:
          #        return {"mode":"nandprg"}
          #    elif len(res) == 0:
          #        print("Device is in Sahara error state, please reboot the device.")
          #        return {"mode": "error"}
    except Exception as e:  # pylint: disable=broad-except
      print(str(e))
    return {"mode": "error"}

  def cmd_info(self, version):
    if self.enter_command_mode(version=version):
      self.serial = self.cmdexec_get_serial_num()
      self.serials = "{:08x}".format(self.serial)
      if version < 3:
        self.hwid = self.cmdexec_get_msm_hwid()
        self.pkhash = self.cmdexec_get_pkhash()
        if self.hwid is not None:
          self.hwidstr = "{:016x}".format(self.hwid)
          self.msm_id = int(self.hwidstr[2:8], 16)
          self.oem_id = int(self.hwidstr[-8:-4], 16)
          self.model_id = int(self.hwidstr[-4:], 16)
          self.oem_str = "{:04x}".format(self.oem_id)
          self.model_id = "{:04x}".format(self.model_id)
          self.msm_str = "{:08x}".format(self.msm_id)
          if self.msm_id in msmids:
            cpustr = f"CPU detected:      \"{msmids[self.msm_id]}\"\n"
          else:
            cpustr = "Unknown CPU, please send log as issue to https://github.com/bkerler/edl\n"
          self.info(f"\nVersion {hex(version)}\n------------------------\n" +
                    f"HWID:              0x{self.hwidstr} (MSM_ID:0x{self.msm_str}," +
                    f"OEM_ID:0x{self.oem_str}," +
                    f"MODEL_ID:0x{self.model_id})\n" +
                    cpustr +
                    f"PK_HASH:           0x{self.pkhash}\n" +
                    f"Serial:            0x{self.serials}\n")
          if self.programmer == "":
            if self.hwidstr in self.loaderdb:
              mt = self.loaderdb[self.hwidstr]
              unfused = False
              for rootcert in root_cert_hash:
                if self.pkhash[0:16] in root_cert_hash[rootcert]:
                  unfused = True
                  break
              if unfused:
                self.info("Possibly unfused device detected, so any loader should be fine...")
                if self.pkhash[0:16] in mt:
                  self.programmer = mt[self.pkhash[0:16]]
                  print(f"Trying loader: {self.programmer}")
                else:
                  for loader in mt:
                    self.programmer = mt[loader]
                    print(f"Possible loader available: {self.programmer}")
                  for loader in mt:
                    self.programmer = mt[loader]
                    print(f"Trying loader: {self.programmer}")
                    break
              elif self.pkhash[0:16] in mt:
                self.programmer = self.loaderdb[self.hwidstr][self.pkhash[0:16]]
                print(f"Detected loader: {self.programmer}")
              else:
                for loader in self.loaderdb[self.hwidstr]:
                  self.programmer = self.loaderdb[self.hwidstr][loader]
                  print(f"Trying loader: {self.programmer}")
                  break
            elif self.hwidstr is not None and self.pkhash is not None:
              msmid = self.hwidstr[:8]
              found = False
              for hwidstr in self.loaderdb:
                if msmid == hwidstr[:8]:
                  if self.pkhash[0:16] in self.loaderdb[hwidstr]:
                    self.programmer = self.loaderdb[hwidstr][self.pkhash[0:16]]
                    print(f"Found loader: {self.programmer}")
                    self.cmd_modeswitch(sahara_mode_t.SAHARA_MODE_COMMAND)
                    return True
                else:
                  if self.pkhash[0:16] in self.loaderdb[hwidstr]:
                    self.programmer = self.loaderdb[hwidstr][self.pkhash[0:16]]
                    print(f"Found possible loader: {self.programmer}")
                    found = True
                if found:
                  self.cmd_modeswitch(sahara_mode_t.SAHARA_MODE_COMMAND)
                  return True
                else:
                  print(
                    f"Couldn't find a loader for given hwid and pkhash ({self.hwidstr}_{self.pkhash[0:16]}" +
                    "_[FHPRG/ENPRG].bin) :(")
                return False
            else:
              print(f"Couldn't find a suitable loader :(")
              return False
      else:
        print(f"\nVersion {hex(version)}\n------------------------\n" +
                  f"Serial:            0x{self.serials}\n")
        if self.programmer=="":
          print("No autodetection of loader possible with sahara version 3 and above :( Aborting.")
          return False
      self.cmd_modeswitch(sahara_mode_t.SAHARA_MODE_COMMAND)
      return True
    return False

  def cmd_reset(self):
    pass

  # TODO: tailor for comma device
  def upload_loader(self, version):
    if self.programmer == "":
      return ""
    try:
      print(f"Uploading loader {self.programmer} ...")
      with open(self.programmer, "rb") as rf:
        programmer = rf.read()
    except Exception as e:  # pylint: disable=broad-except
      self.error(str(e))
      sys.exit()

    if not self.cmd_hello(sahara_mode_t.SAHARA_MODE_IMAGE_TX_PENDING, version=version):
      return ""
    try:
      datalen = len(programmer)
      done = False
      loop = 0
      while datalen >= 0 or done:
        resp = self.get_rsp()
        if "cmd" in resp:
          cmd = resp["cmd"]
        else:
          cmd = None
        if cmd == cmd_t.SAHARA_DONE_REQ:
          if self.cmd_done():
            return self.mode  # Do NOT remove
          else:
            print("Timeout while uploading loader. Wrong loader ?")
            return ""
        elif cmd in [cmd_t.SAHARA_64BIT_MEMORY_READ_DATA,cmd_t.SAHARA_READ_DATA]:
          if cmd == cmd_t.SAHARA_64BIT_MEMORY_READ_DATA:
            self.bit64 = True
            if loop == 0:
              self.info("64-Bit mode detected.")
          elif cmd == cmd_t.SAHARA_READ_DATA:
            self.bit64 = False
            if loop == 0:
              self.info("32-Bit mode detected.")
          pkt = resp["data"]
          self.id = pkt.image_id
          #if self.id == 0x7:
          #  self.mode = "nandprg"
          #  if loop == 0:
          #    self.info("NAND mode detected, uploading...")
          #elif self.id == 0xB:
          #  self.mode = "enandprg"
          #  if loop == 0:
          #    self.info("eNAND mode detected, uploading...")
          if self.id >= 0xC:
            self.mode = "firehose"
            if loop == 0:
              print("Firehose mode detected, uploading...")
          else:
            print(f"Unknown sahara id: {self.id}")
            return "error"
          loop+=1
          data_offset = pkt.data_offset
          data_len = pkt.data_len
          if data_offset + data_len > len(programmer):
            while len(programmer) < data_offset + data_len:
              programmer += b"\xFF"
          data_to_send = programmer[data_offset:data_offset + data_len]
          self.cdc.write(data_to_send)
          datalen -= data_len
        elif cmd == cmd_t.SAHARA_END_TRANSFER:
          pkt = resp["data"]
          if pkt.image_tx_status == status_t.SAHARA_STATUS_SUCCESS:
            if self.cmd_done():
              print("Loader successfully uploaded.")
            else:
              print("Error on uploading Loader.")
              sys.exit(1)
            return self.mode
          #else:
          #  print(self.get_error_desc(pkt.image_id))
          #  return "error"
        else:
          print("Unknown response received on uploading loader.")
          sys.exit(1)
    except Exception as e:  # pylint: disable=broad-except
      print("Unexpected error on uploading, maybe signature of loader wasn't accepted ?\n" + str(e))
      return ""
    return self.mode

  def enter_command_mode(self, version=2):
    if not self.cmd_hello(sahara_mode_t.SAHARA_MODE_COMMAND, version=version):
      return False
    res = self.get_rsp()
    if "cmd" in res:
      if res["cmd"] == cmd_t.SAHARA_END_TRANSFER:
        if "data" in res:
          pkt = res["data"]
          #self.error(self.get_error_desc(pkt.image_tx_status))
          print("Error in enter_command_mode")
          return False
      elif res["cmd"] == cmd_t.SAHARA_CMD_READY:
        return True
    return False
  
  def cmd_hello(self, mode, version_min=1, max_cmd_len=0, version=2):  # CMD 0x1, RSP 0x2
    cmd = cmd_t.SAHARA_HELLO_RSP
    length = 0x30
    #version = SAHARA_VERSION
    responsedata = pack("<IIIIIIIIIIII", cmd, length, version, version_min, max_cmd_len, mode, 1, 2, 3, 4, 5, 6)
    try:
      self.cdc.write(responsedata)
      return True
    except Exception as e:  # pylint: disable=broad-except
      self.error(str(e))
      return False

  # TODO: taior for comma device
  def get_rsp(self):
    try:
      data = self.cdc.read()
      if data == b'':
          return {}
      if b"<?xml" in data:
          return {"firehose":"yes"}
      pkt = self.ch.pkt_cmd_hdr(data)
      if pkt.cmd == cmd_t.SAHARA_HELLO_REQ:
          return {"cmd":pkt.cmd,"data":self.ch.pkt_hello_req(data)}
      elif pkt.cmd == cmd_t.SAHARA_DONE_RSP:
          return {"cmd": pkt.cmd, "data":self.ch.pkt_done(data)}
      elif pkt.cmd == cmd_t.SAHARA_END_TRANSFER:
          return {"cmd": pkt.cmd, "data": self.ch.pkt_image_end(data)}
      elif pkt.cmd == cmd_t.SAHARA_64BIT_MEMORY_READ_DATA:
          self.bit64 = True
          return {"cmd": pkt.cmd, "data": self.ch.pkt_read_data_64(data)}
      elif pkt.cmd == cmd_t.SAHARA_READ_DATA:
          self.bit64 = False
          return {"cmd": pkt.cmd, "data": self.ch.pkt_read_data(data)}
      elif pkt.cmd == cmd_t.SAHARA_64BIT_MEMORY_DEBUG:
          self.bit64 = True
          return {"cmd": pkt.cmd, "data": self.ch.pkt_memory_debug_64(data)}
      elif pkt.cmd == cmd_t.SAHARA_MEMORY_DEBUG:
          self.bit64 = False
          return {"cmd": pkt.cmd, "data": self.ch.pkt_memory_debug(data)}
      elif pkt.cmd == cmd_t.SAHARA_EXECUTE_RSP:
          return {"cmd": pkt.cmd, "data": self.ch.pkt_execute_rsp_cmd(data)}
      elif pkt.cmd == cmd_t.SAHARA_CMD_READY or pkt.cmd == cmd_t.SAHARA_RESET_RSP:
          return {"cmd": pkt.cmd, "data": None }
      return {}
    except Exception as e:  # pylint: disable=broad-except
      print(str(e))
      return {}

  def cmd_done(self):
    if self.cdc.write(pack("<II", cmd_t.SAHARA_DONE_REQ, 0x8)):
      res = self.get_rsp()
      time.sleep(0.3)
      if "cmd" in res:
        cmd = res["cmd"]
        if cmd == cmd_t.SAHARA_DONE_RSP:
          return True
        elif cmd == cmd_t.SAHARA_END_TRANSFER:
          if "data" in res:
            pkt = res["data"]
            if pkt.image_tx_status == status_t.SAHARA_NAK_INVALID_CMD:
              print("Invalid Transfer command received.")
              return False
        else:
          print(f"Received invalid response {cmd}.")
    return False

  def get_error_desc(self):
    pass

  def cmd_exec(self, mcmd):  # CMD 0xD, RSP 0xE, CMD2 0xF
    # Send request
    data = pack("<III", cmd_t.SAHARA_EXECUTE_REQ, 0xC, mcmd)
    self.cdc.write(data)
    # Get info about request
    res = self.get_rsp()
    if "cmd" in res:
      cmd = res["cmd"]
      if res["cmd"] == cmd_t.SAHARA_EXECUTE_RSP:
        pkt = res["data"]
        data = pack("<III", cmd_t.SAHARA_EXECUTE_DATA, 0xC, mcmd)
        self.cdc.write(data)
        payload = self.cdc.usbread(pkt.data_len)
        return payload
      elif cmd == cmd_t.SAHARA_END_TRANSFER:
        pkt = res["data"]
        print("error in cmd_exec!")
        #self.error(self.get_error_desc(pkt.image_tx_status))
      return None
    return res
  
  def cmdexec_get_serial_num(self):
    res = self.cmd_exec(exec_cmd_t.SAHARA_EXEC_CMD_SERIAL_NUM_READ)
    return int.from_bytes(res,'little')
  
  def cmdexec_get_msm_hwid(self):
    res = self.cmd_exec(exec_cmd_t.SAHARA_EXEC_CMD_MSM_HW_ID_READ)
    if res is not None:
      return int.from_bytes(res[:8],'little')
    return None
  
  def cmdexec_get_pkhash(self):
    try:
      res = self.cmd_exec(exec_cmd_t.SAHARA_EXEC_CMD_OEM_PK_HASH_READ)
      idx=res[4:].find(res[:4])
      if idx!=-1:
        res=res[:4+idx]
      return res.hex()
    except Exception as e:  # pylint: disable=broad-except
      print(str(e))
      return None
  
  def cmd_modeswitch(self, mode):
    data = pack("<III", cmd_t.SAHARA_SWITCH_MODE, 0xC, mode)
    self.cdc.write(data)
  


