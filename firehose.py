"""
class cfg()

connect() what does it connect to?
  - xml_handler object
  - serial number?
  - get_supported_functions()

configure()
  - xmlsend()
  - self.moduels.edlauth()
  - cmd_read_buffer()
  - parse_storage()
    - get_storageinfo()
  - getluns()

cmd_reset()
"""

import os
import json
import time


class response:
  resp = False
  data = b""
  error = ""
  log = None

  def __init__(self, resp=False, data=b""):
    self.resp = resp
    self.data = data

class firehose:
  class cfg:
    TargetName = ""
    Version = ""
    ZLPAwareHost = 1
    SkipStorageInit = 0
    SkipWrite = 0
    MaxPayloadSizeToTargetInBytes = 1048576
    MaxPayloadSizeFromTargetInBytes = 8192
    MaxXMLSizeInBytes = 4096
    bit64 = True

    total_blocks = 0
    num_physical = 0
    block_size = 0
    SECTOR_SIZE_IN_BYTES = 0
    MemoryName = "eMMC"
    prod_name = "Unknown"
    maxlun = 99

  def __init__(self, cdc, xml, cfg, devicemodel, serial, luns, args):
    self.cdc = cdc
    #self.lasterror = b""
    #self.loglevel = loglevel
    #self.args = args
    #self.xml = xml
    #self.cfg = cfg
    #self.prog = 0
    #self.progtime = 0
    #self.progpos = 0
    #self.pk = None
    #self.modules = None
    #self.serial = serial
    #self.devicemodel = devicemodel
    #self.skipresponse = skipresponse
    #self.luns = luns
    self.supported_functions = []
    #self.lunsizes = {}

  def connect(self):
    v = b'-1'
    self.cdc.timeout = 50
    info = []
    while v != b'':
      try:
        v = self.cdc.read(timeout=None)
        if (b"response" in v and b"</data>" in v) or v == b'':
          break
        data = self.xml.getlog(v)
        if len(data) > 0:
          info.append(data[0])
        if not info:
          break
      except Exception as err:  # pylint: disable=broad-except
        pass

    #if info == [] or (len(info) > 0 and 'ERROR' in info[0]):
    #  if len(info) > 0:
    #    self.debug(info[0])
    if len(info) > 0:
      supfunc = False
      for line in info:
        self.info(line)
        if "chip serial num" in line.lower():
          try:
            serial = line.split("0x")[1][:-1]
            if ")" in serial:
                serial=serial[:serial.rfind(")")]
            self.serial = int(serial, 16)
          except Exception as err:  # pylint: disable=broad-except
            self.debug(str(err))
            serial = line.split(": ")[2]
            self.serial = int(serial.split(" ")[0])
        if supfunc and "end of supported functions" not in line.lower():
          rs = line.replace("\n", "")
          if rs != "":
            rs = rs.replace("INFO: ", "")
            self.supported_functions.append(rs)
        if "supported functions" in line.lower():
          supfunc = True
          if "program" in line.lower():
            idx = line.find("Functions: ")
            if idx != -1:
              v = line[idx + 11:].split(" ")
              for val in v:
                if val != "":
                  self.supported_functions.append(val)
              supfunc = False
      try:
        if os.path.exists(self.cfg.programmer):
          data = open(self.cfg.programmer, "rb").read()
          for cmd in [b"demacia", b"setprojmodel", b"setswprojmodel", b"setprocstart", b"SetNetType", b"checkntfeature"]:
            if cmd in data:
              self.supported_functions.append(cmd.decode('utf-8'))
        state = {
            "supported_functions": self.supported_functions,
            "programmer": self.cfg.programmer,
            "serial": self.serial
        }
        if os.path.exists("edl_config.json"):
          data = json.loads(open("edl_config.json","rb").read().decode('utf-8'))
          if "serial" in data and data["serial"]!=state["serial"]:
            open("edl_config.json", "w").write(json.dumps(state))
          else:
            self.supported_functions = data["supported_functions"]
            self.cfg.programmer = data["programmer"]
        else:
          open("edl_config.json", "w").write(json.dumps(state))
        #if "001920e101cf0000_fa2836525c2aad8a_fhprg.bin" in self.cfg.programmer:
        #  self.devicemodel = '20111'
        #elif "000b80e100020000_467f3020c4cc788d_fhprg.bin" in self.cfg.programmer:
        #  self.devicemodel = '22111'
      except:
          pass
    #elif self.serial is None or self.supported_functions is []:
    #  try:
    #    if os.path.exists("edl_config.json"):
    #      pinfo = json.loads(open("edl_config.json", "rb").read())
    #      if not self.supported_functions:
    #        if "supported_functions" in pinfo:
    #          self.supported_functions = pinfo["supported_functions"]
    #      if self.serial is None:
    #        if "serial" in pinfo:
    #          self.serial = pinfo["serial"]
    #      else:
    #        self.get_supported_functions()
    #  except:
    #    self.get_supported_functions()
    #    pass
    return self.supported_functions
  
  # TODO: tailor to comma device
  def get_supported_functions(self):
    pass

  def configure(self, lvl):
    # TODO: configure the cfg in firhose_client
    if self.cfg.SECTOR_SIZE_IN_BYTES == 0:
      self.cfg.SECTOR_SIZE_IN_BYTES = 4096
    connectcmd = f"<?xml version=\"1.0\" encoding=\"UTF-8\" ?><data>" + \
                  f"<configure MemoryName=\"{self.cfg.MemoryName}\" " + \
                  f"Verbose=\"0\" " + \
                  f"AlwaysValidate=\"0\" " + \
                  f"MaxDigestTableSizeInBytes=\"2048\" " + \
                  f"MaxPayloadSizeToTargetInBytes=\"{str(self.cfg.MaxPayloadSizeToTargetInBytes)}\" " + \
                  f"ZLPAwareHost=\"{str(self.cfg.ZLPAwareHost)}\" " + \
                  f"SkipStorageInit=\"{str(int(self.cfg.SkipStorageInit))}\" " + \
                  f"SkipWrite=\"{str(int(self.cfg.SkipWrite))}\"/>" + \
                  "</data>"
    # TODO: add xmlsend()
    rsp = self.xmlsend(connectcmd)
    #if not rsp.resp:
    #  if rsp.error == "":
    #    try:
    #      if "MemoryName" in rsp.data:
    #        self.cfg.MemoryName = rsp.data["MemoryName"]
    #    except TypeError:
    #      print("!DEBUG! rsp.data: '%s'" % (rsp.data,))
    #      return self.configure(lvl + 1)
    #    if "MaxPayloadSizeFromTargetInBytes" in rsp.data:
    #      self.cfg.MaxPayloadSizeFromTargetInBytes = int(rsp.data["MaxPayloadSizeFromTargetInBytes"])
    #    if "MaxPayloadSizeToTargetInBytes" in rsp.data:
    #      self.cfg.MaxPayloadSizeToTargetInBytes = int(rsp.data["MaxPayloadSizeToTargetInBytes"])
    #    if "MaxPayloadSizeToTargetInBytesSupported" in rsp.data:
    #      self.cfg.MaxPayloadSizeToTargetInBytesSupported = int(
    #          rsp.data["MaxPayloadSizeToTargetInBytesSupported"])
    #    if "TargetName" in rsp.data:
    #      self.cfg.TargetName = rsp.data["TargetName"]
    #    return self.configure(lvl + 1)
    #  for line in rsp.error:
    #    if "Not support configure MemoryName eMMC" in line:
    #      print("eMMC is not supported by the firehose loader. Trying UFS instead.")
    #      self.cfg.MemoryName = "UFS"
    #      return self.configure(lvl + 1)
    #    elif "Only nop and sig tag can be" in line:
    #      print("Xiaomi EDL Auth detected.")
    #      try:
    #        # TODO: add modules
    #        self.modules = modules(fh=self, serial=self.serial,
    #                                supported_functions=self.supported_functions,
    #                                loglevel=self.__logger.level,
    #                                devicemodel=self.devicemodel, args=self.args)
    #      except Exception as err:  # pylint: disable=broad-except
    #        self.modules = None
    #      if self.modules.edlauth():
    #        rsp = self.xmlsend(connectcmd)
    #        return rsp.resp
    #      else:
    #        print("Error on EDL Authentification")
    #        return False
    #    if "MaxPayloadSizeToTargetInBytes" in rsp.data:
    #      try:
    #        self.cfg.MemoryName = rsp.data["MemoryName"]
    #        self.cfg.MaxPayloadSizeToTargetInBytes = int(rsp.data["MaxPayloadSizeToTargetInBytes"])
    #        self.cfg.MaxPayloadSizeToTargetInBytesSupported = int(
    #            rsp.data["MaxPayloadSizeToTargetInBytesSupported"])
    #        if "MaxXMLSizeInBytes" in rsp.data:
    #          self.cfg.MaxXMLSizeInBytes = int(rsp.data["MaxXMLSizeInBytes"])
    #        else:
    #          self.cfg.MaxXMLSizeInBytes = 4096
    #        if "MaxPayloadSizeFromTargetInBytes" in rsp.data:
    #          self.cfg.MaxPayloadSizeFromTargetInBytes = int(rsp.data["MaxPayloadSizeFromTargetInBytes"])
    #        else:
    #          self.cfg.MaxPayloadSizeFromTargetInBytes = 4096
    #        if "TargetName" in rsp.data:
    #          self.cfg.TargetName = rsp.data["TargetName"]
    #        else:
    #          self.cfg.TargetName = "Unknown"
    #        if "MSM" not in self.cfg.TargetName:
    #          self.cfg.TargetName = "MSM" + self.cfg.TargetName
    #        if "Version" in rsp.data:
    #          self.cfg.Version = rsp.data["Version"]
    #        else:
    #          self.cfg.Version = "Unknown"
    #        if lvl == 0:
    #          return self.configure(lvl + 1)
    #        else:
    #          self.error(f"Error:{rsp}")
    #          sys.exit()
    #      except Exception as e:
    #          pass
    #    elif "ERROR" in line or "WARN" in line:
    #      if "ERROR" in line:
    #        print(line)
    #        sys.exit()
    #      elif "WARN" in line:
    #        self.warning(line)
    if rsp.resp:
      info = self.cdc.read(timeout=1)
      #if isinstance(rsp.resp, dict):
      #  field = rsp.resp
      #  if "MemoryName" not in field:
      #    # print(rsp[1])
      #    field["MemoryName"] = "eMMC"
      #  if "MaxXMLSizeInBytes" not in field:
      #    field["MaxXMLSizeInBytes"] = "4096"
      #    self.warning("Couldn't detect MaxPayloadSizeFromTargetinBytes")
      #  if "MaxPayloadSizeToTargetInBytes" not in field:
      #    field["MaxPayloadSizeToTargetInBytes"] = "1038576"
      #  if "MaxPayloadSizeToTargetInBytesSupported" not in field:
      #    field["MaxPayloadSizeToTargetInBytesSupported"] = "1038576"
      #  if field["MemoryName"].lower() != self.cfg.MemoryName.lower():
      #    self.warning("Memory type was set as " + self.cfg.MemoryName + " but device reported it is " +
      #                  field["MemoryName"] + " instead.")
      #  self.cfg.MemoryName = field["MemoryName"]
      #  if "MaxPayloadSizeToTargetInBytes" in field:
      #    self.cfg.MaxPayloadSizeToTargetInBytes = int(field["MaxPayloadSizeToTargetInBytes"])
      #  else:
      #    self.cfg.MaxPayloadSizeToTargetInBytes = 1048576
      #  if "MaxPayloadSizeToTargetInBytesSupported" in field:
      #    self.cfg.MaxPayloadSizeToTargetInBytesSupported = int(
      #        field["MaxPayloadSizeToTargetInBytesSupported"])
      #  else:
      #    self.cfg.MaxPayloadSizeToTargetInBytesSupported = 1048576
      #  if "MaxXMLSizeInBytes" in field:
      #    self.cfg.MaxXMLSizeInBytes = int(field["MaxXMLSizeInBytes"])
      #  else:
      #    self.cfg.MaxXMLSizeInBytes = 4096
      #  if "MaxPayloadSizeFromTargetInBytes" in field:
      #    self.cfg.MaxPayloadSizeFromTargetInBytes = int(field["MaxPayloadSizeFromTargetInBytes"])
      #  else:
      #    self.cfg.MaxPayloadSizeFromTargetInBytes = self.cfg.MaxXMLSizeInBytes
      #    self.warning("Couldn't detect MaxPayloadSizeFromTargetinBytes")
      #  if "TargetName" in field:
      #    self.cfg.TargetName = field["TargetName"]
      #    if "MSM" not in self.cfg.TargetName:
      #        self.cfg.TargetName = "MSM" + self.cfg.TargetName
      #  else:
      #    self.cfg.TargetName = "Unknown"
      #    self.warning("Couldn't detect TargetName")
      #  if "Version" in field:
      #    self.cfg.Version = field["Version"]
      #  else:
      #    self.cfg.Version = 0
      #    self.warning("Couldn't detect Version")
      print(f"TargetName={self.cfg.TargetName}")
      print(f"MemoryName={self.cfg.MemoryName}")
      print(f"Version={self.cfg.Version}")
      print("Trying to read first storage sector...")
      rsp = self.cmd_read_buffer(0, 1, 1, False)
      print("Running configure...")
      #if not rsp.resp and self.args["--memory"] is None:
      #  for line in rsp.error:
      #    if "Failed to set the IO options" in line:
      #        self.warning(
      #            "Memory type eMMC doesn't seem to match (Failed to init). Trying to use NAND instead.")
      #        self.cfg.MemoryName = "nand"
      #        return self.configure(0)
      #    elif "Failed to open the SDCC Device" in line:
      #        self.warning(
      #            "Memory type eMMC doesn't seem to match (Failed to init). Trying to use UFS instead.")
      #        self.cfg.MemoryName = "UFS"
      #        return self.configure(0)
      #    elif "Failed to initialize (open whole lun) UFS Device slot" in line:
      #        self.warning(
      #            "Memory type UFS doesn't seem to match (Failed to init). Trying to use eMMC instead.")
      #        self.cfg.MemoryName = "eMMC"
      #        return self.configure(0)
      #    if "Attribute \'SECTOR_SIZE_IN_BYTES\'=4096 must be equal to disk sector size 512" in line \
      #            or "different from device sector size (512)" in line:
      #      self.cfg.SECTOR_SIZE_IN_BYTES = 512
      #      return self.configure(0)
      #    elif "Attribute \'SECTOR_SIZE_IN_BYTES\'=512 must be equal to disk sector size 4096" in line \
      #            or "different from device sector size (4096)" in line:
      #      self.cfg.SECTOR_SIZE_IN_BYTES = 4096
      #      return self.configure(0)
    self.parse_storage()
    #for function in self.supported_functions:
    #  if function == "checkntfeature":
    #    if type(self.devicemodel)==list:
    #      self.devicemodel=self.devicemodel[0]
    #    self.nothing = nothing(fh=self, projid=self.devicemodel, serial=self.serial,
    #                            supported_functions=self.supported_functions,
    #                            loglevel=self.loglevel)
    #    if self.nothing is not None:
    #      self.nothing.ntprojectverify()
    self.luns = self.getluns(self.args)
    return True

  def cmd_read_buffer(self):
    pass

  def parse_storage(self):
    storageinfo = self.cmd_getstorageinfo()
    if storageinfo is None or storageinfo.resp and len(storageinfo.data) == 0:
      return False
    info = storageinfo.data
    if "UFS Inquiry Command Output" in info:
      self.cfg.prod_name = info["UFS Inquiry Command Output"]
      print(info)
    if "UFS Erase Block Size" in info:
      self.cfg.block_size = int(info["UFS Erase Block Size"], 16)
      print(info)
      self.cfg.MemoryName = "UFS"
      self.cfg.SECTOR_SIZE_IN_BYTES = 4096
    if "UFS Boot Partition Enabled" in info:
      print(info["UFS Boot Partition Enabled"])
    if "UFS Total Active LU" in info:
      self.cfg.maxlun = int(info["UFS Total Active LU"], 16)
    if "SECTOR_SIZE_IN_BYTES" in info:
      self.cfg.SECTOR_SIZE_IN_BYTES = int(info["SECTOR_SIZE_IN_BYTES"])
    if "num_physical_partitions" in info:
      self.cfg.num_physical = int(info["num_physical_partitions"])
    return True

  def cmd_getstorageinfo(self):
    data = "<?xml version=\"1.0\" ?><data><getstorageinfo physical_partition_number=\"0\"/></data>"
    val = self.xmlsend(data)
    if val.data == '' and val.log == '' and val.resp:
      return None
    if isinstance(val.data, dict):
      if "bNumberLu" in val.data:
          self.cfg.maxlun = int(val.data["bNumberLu"])
    if val.resp:
      if val.log is not None:
        res = {}
        for value in val.log:
          v = value.split("=")
          if len(v) > 1:
            res[v[0]] = v[1]
          else:
            if "\"storage_info\"" in value:
              try:
                info = value.replace("INFO:", "")
                si = json.loads(info)["storage_info"]
              except Exception as err:  # pylint: disable=broad-except
                self.debug(str(err))
                continue
              self.info("Storage report:")
              for sii in si:
                self.info(f"{sii}:{si[sii]}")
              if "total_blocks" in si:
                self.cfg.total_blocks = si["total_blocks"]
              if "num_physical" in si:
                self.cfg.num_physical = si["num_physical"]
                self.cfg.maxlun = self.cfg.num_physical
              if "block_size" in si:
                self.cfg.block_size = si["block_size"]
              if "page_size" in si:
                self.cfg.SECTOR_SIZE_IN_BYTES = si["page_size"]
              if "mem_type" in si:
                self.cfg.MemoryName = si["mem_type"]
              if "prod_name" in si:
                self.cfg.prod_name = si["prod_name"]
            else:
              v = value.split(":")
              if len(v) > 1:
                  res[v[0]] = v[1].lstrip(" ")
            return response(resp=val.resp, data=res)
        return response(resp=val.resp, data=val.data)
    #else:
    #    if val.error:
    #        for v in val.error:
    #            if "Failed to open the SDCC Device" in v:
    #                self.cfg.MemoryName = "ufs"
    #                self.configure(0)
    #                return self.cmd_getstorageinfo()
    #    self.warning("GetStorageInfo command isn't supported.")
    #    return None

  def get_storageinfo(self):
    pass

  def getluns(self, argument):
    #if argument["--lun"] is not None:
    #  return [int(argument["--lun"])]
    luns = []
    if self.cfg.MemoryName.lower() == "ufs":
      for i in range(0, self.cfg.maxlun):
        luns.append(i)
    #else:
    #  luns = [0]
    return luns 

  def cmd_reset(self, mode="reset"):
    if mode is None:
      mode = "reset"
    data = "<?xml version=\"1.0\" ?><data><power value=\"" + mode + "\"/></data>"
    val = self.xmlsend(data)
    try:
      v = None
      while v != b'':
        v = self.cdc.read(timeout=None)
        if v != b'':
          resp = self.xml.getlog(v)[0]
        else:
          break
        print(resp)
    except Exception as err:
      print(str(err))
      pass
    if val.resp:
      print("Reset succeeded.")
      return True
    else:
      print("Reset failed: " + val.error)
      return False

  def xmlsend(self, data, skipresponse=False) -> response:
    self.cdc.flush()
    self.cdc.xmlread = True
    if isinstance(data, bytes) or isinstance(data, bytearray):
      self.cdc.write(data[:self.cfg.MaxXMLSizeInBytes])
    else:
      self.cdc.write(bytes(data, 'utf-8')[:self.cfg.MaxXMLSizeInBytes])
    rdata = bytearray()
    counter = 0
    timeout = 3
    if not skipresponse:
      while b"<response value" not in rdata:
        try:
          tmp = self.cdc.read(timeout=None)
          if tmp == b"" in rdata:
            counter += 1
            time.sleep(0.05)
            if counter > timeout:
              break
          rdata += tmp
        except Exception as err:
          print(err)
          return response(resp=False, error=str(err))
      try:
        if b"raw hex token" in rdata:
          rdata = rdata
        try:
          resp = self.xml.getresponse(rdata)
          status = self.getstatus(resp)
          if "rawmode" in resp:
            if resp["rawmode"] == "false":
              if status:
                log = self.xml.getlog(rdata)
                return response(resp=status, data=rdata, log=log)
              else:
                error = self.xml.getlog(rdata)
                return response(resp=status, error=error, data=resp, log=error)
          else:
            if status:
              if b"log value=" in rdata:
                log = self.xml.getlog(rdata)
                return response(resp=resp, data=rdata, log=log)
              return response(resp=status, data=rdata)
        except Exception as e:  # pylint: disable=broad-except
          rdata = bytes(self.decoder(rdata), 'utf-8')
          resp = self.xml.getresponse(rdata)
        status = self.getstatus(resp)
        if status:
          return response(resp=True, data=resp)
        else:
          error = ""
          if b"<log value" in rdata:
            error = self.xml.getlog(rdata)
          return response(resp=False, error=error, data=resp)
      except Exception as err:
        print(str(err))
        #if isinstance(rdata, bytes) or isinstance(rdata, bytearray):
        #  try:
        #    self.debug("Error on getting xml response:" + rdata.decode('utf-8'))
        #  except Exception as err:
        #    self.debug("Error on getting xml response:" + hexlify(rdata).decode('utf-8') +
        #                ", Error: " + str(err))
        #elif isinstance(rdata, str):
        #    self.debug("Error on getting xml response:" + rdata)
        return response(resp=False, error=rdata)
    else:
        return response(resp=True, data=rdata)