"""
connect()
  - firehose() object:
    - self.firehose.connect()
    - self.firehose.configure()
    - self.firehose.modules (initialize from modules file)

handle_firehose()
  - reset:
    - check_param
    - self.firehose.cmd_reset()

modules() object
  - figure out what this does
"""

import sys

from firehose import firehose
from xmlparser import xmlparser
from utils import getint
from qualcomm_config import memory_type, sochw, msmids

try:
    # TODO: init
    from edlclient.Library.Modules.init import modules
except ImportError as e:
    pass

class firehose_client:
  def __init__(self, arguments, cdc, sahara):
    # TODO: investigate what is needed
    # TODO: remove arguments
    self.cdc = cdc
    self.sahara = sahara
    self.arguments = arguments

    self.cfg = firehose.cfg()
    #if not arguments["--memory"] is None:
    #    self.cfg.MemoryName = arguments["--memory"].lower()
    self.cfg.MemoryName = "UFS"
    self.cfg.ZLPAwareHost = 1
    #self.cfg.SkipStorageInit = arguments["--skipstorageinit"]
    #self.cfg.SkipStorageInit = 
    #self.cfg.SkipWrite = arguments["--skipwrite"]
    #self.cfg.MaxPayloadSizeToTargetInBytes = getint(arguments["--maxpayload"])
    #self.cfg.SECTOR_SIZE_IN_BYTES = getint(arguments["--sectorsize"])
    self.cfg.bit64 = sahara.bit64
    devicemodel = ""
    skipresponse = False
    #if "--skipresponse" in arguments:
    #    if arguments["--skipresponse"]:
    #        skipresponse = True
    #if "--devicemodel" in arguments:
    #    if arguments["--devicemodel"] is not None:
    #        devicemodel = arguments["--devicemodel"]
    self.cfg.programmer = self.sahara.programmer
    self.firehose = firehose(cdc=cdc, xml=xmlparser(), cfg=self.cfg,
                              serial=sahara.serial, luns=self.getluns())
    self.connected = False

  def connect(self, sahara):
    self.firehose.connect()
    #if "hwid" in dir(sahara):
      #if sahara.hwid is not None:
      #  hwid = (sahara.hwid >> 32) & 0xFFFFFF
      #  socid = ((sahara.hwid >> 32) >> 16)
      #  if hwid in msmids:
      #    self.target_name = msmids[hwid]
      #    self.info(f"Target detected: {self.target_name}")
      #    if self.cfg.MemoryName == "":
      #      if self.target_name in memory_type.preferred_memory:
      #        type = memory_type.preferred_memory[self.target_name]
      #        #if type == memory_type.nand:
      #        #  self.cfg.MemoryName = "nand"
      #        #if type == memory_type.spinor:
      #        #  self.cfg.MemoryName = "spinor"
      #        #elif type == memory_type.emmc:
      #        #  self.cfg.MemoryName = "eMMC"
      #        if type == memory_type.ufs:
      #          self.cfg.MemoryName = "UFS"
      #        print("Based on the chipset, we assume " +
      #                      self.cfg.MemoryName + " as default memory type..., if it fails, try using " +
      #                      "--memory\" with \"UFS\",\"NAND\" or \"spinor\" instead !")
      #      elif socid in sochw:
      #          self.target_name = sochw[socid].split(",")[0]

    # We assume ufs is fine (hopefully), set it as default
    if self.cfg.MemoryName == "":
        if "ufs" in self.firehose.supported_functions:
          print(
              "No --memory option set, we assume \"UFS\" as default ..., if it fails, try using \"--memory\" " +
              "with \"UFS\",\"NAND\" or \"spinor\" instead !")
          self.cfg.MemoryName = "UFS"
        #else:
        #  print(
        #      "No --memory option set, we assume \"eMMC\" as default ..., if it fails, try using \"--memory\" " +
        #      "with \"UFS\",\"NAND\" or \"spinor\" instead !")
        #  self.cfg.MemoryName = "eMMC"
    if self.firehose.configure(0):
      funcs = "Supported functions:\n-----------------\n"
      for function in self.firehose.supported_functions:
          funcs += function + ","
      funcs = funcs[:-1]
      print(funcs)
      self.target_name = self.firehose.cfg.TargetName
      self.connected = True
      #try:
      #    if self.firehose.modules is None:
      #      self.firehose.modules = modules(fh=self.firehose, serial=self.firehose.serial,
      #                                      supported_functions=self.firehose.supported_functions,
      #                                      loglevel=self.__logger.level,
      #                                      devicemodel=self.firehose.devicemodel, args=self.arguments)
      #except Exception as err:  # pylint: disable=broad-except
      #    self.firehose.modules = None
    return self.connected
  
  def getluns(self):
    #if argument["--lun"] is not None:
    #  return [int(argument["--lun"])]
    luns = []
    if self.cfg.MemoryName.lower() == "ufs":
      for i in range(0, self.cfg.maxlun):
        luns.append(i)
    else:
      luns = [0]
    return luns
  
  def handle_firehose(self, cmd, options):
    if cmd == "reset":
      mode = "reset"
      #if not self.check_param(["--resetmode"]):
      #  return False
      return self.firehose.cmd_reset()
    else: 
      print("Doesn't support right now")
      sys.exit(1)
