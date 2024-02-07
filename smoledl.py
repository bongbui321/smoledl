import sys
from docopt import docopt

from usblib import usb_class
from sahara import sahara
from sahara_defs import cmd_t
from firehose_client import firehose_client

#default_ids = [
#  [0x05c6, 0x9008, -1],
#  [0x0fce, 0x9dde, -1],
#  [0x0fce, 0xade5, -1],
#  [0x05c6, 0x900e, -1],
#  [0x05c6, 0x9025, -1],
#  [0x1199, 0x9062, -1],
#  [0x1199, 0x9070, -1],
#  [0x1199, 0x9090, -1],
#  [0x0846, 0x68e0, -1],
#  [0x19d2, 0x0076, -1]
#]

if len(sys.argv) > 1:
  args = {sys.argv[1] : True}
  print(args)
else:
  print("GIVE COMMAND")
  sys.exit(1)


def parse_cmd(rargs):
  cmds = ["w", "e", "setactiveslot", "reset"]
  for cmd in cmds:
    if cmd in rargs:
      return cmd
  return ""

def parse_option(rargs):
  options = {}
  for arg in rargs:
    if "--" in arg or "<" in arg:
      options[arg] = rargs[arg]
  return options

class main:
  def __init__(self):
    self.cdc = None
    self.sahara = None
    self.vid = None 
    self.pid = None
    self.serial_number = None
    self.portconfig = [[0x05c6, 0x9008, -1]] # vendorId, productId, interface
    #self.portconfig = default_ids
  
  def doconnect(self):
    while not self.cdc.connected:
      self.cdc.connected = self.cdc.connect()
      if not self.cdc.connected:
        sys.stdout.write('.')
      else:
        print(">>> Device detected <<<")
        try:
          resp = self.sahara.connect()
          self.vid = self.cdc.vid
          self.pid = self.cdc.pid
        except Exception as err:
          print(err)
          continue
        if "mode" in resp:
          mode = resp["mode"]
          print(f"Mode detected: {mode}")
          return resp
    return {"mode": "error"}

  def run(self):
    mode = ""

    self.cdc = usb_class(portconfig=self.portconfig)
    self.sahara = sahara(self.cdc)
    self.sahara.programmer = ""

    resp = None
    self.cdc.timeout = 1500
    conninfo = self.doconnect()
    mode = conninfo["mode"]

    if not "data" in conninfo:
      version = 2
    else:
      version = conninfo["data"].version

    if mode == "sahara":
      cmd = conninfo["cmd"]
      if cmd == cmd_t.SAHARA_HELLO_REQ:
        if "data" in conninfo:
          sahara_info = self.sahara.cmd_info(version=version)
          if sahara_info is not None:
            resp = self.sahara.connect()
            mode = resp["mode"]
            #if "data" in resp:
            #  data = resp["data"]
            if mode == "sahara":
              mode = self.sahara.upload_loader(version=version)
          else:
            print("Error on sahara handshake, resetting")
            self.sahara.cmd_reset()
            sys.exit(1)
    if mode == "error":
      print("Connection detected, quitting.")
      sys.exit(1)
    if mode == "firehose":
      self.cdc.timeout = None
      cmd = parse_cmd(args)
      fh = firehose_client(args, self.cdc, self.sahara)
      options = parse_option(args)
      if cmd != "":
        print("Trying to connect to firehose loader...")
        if fh.connect(sahara):
          fh.handle_firehose(cmd, options)
    else:
      print("ERROR: Don't work with non-firehose protocol")
      sys.exit(1)
  
if __name__ == "__main__":
  base = main()
  base.run()
