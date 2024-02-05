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
from xmlparser import xmlparser

class firehose:
  class cfg:
    pass
  def __init__(self, cdc, xml, cfg, devicemodel, args):
    self.cdc = cdc
    self.xml = xml
    self.cfg = cfg
    self.devicemodel = devicemodel
    self.firehose = None # firehose()
  
  def connect(self):
    pass

  def configure(self):
    pass
  
  def xmlsend(self):
    pass

  def get_supported_functions(self):
    pass

  def cmd_read_buffer(self):
    pass

  def parse_srorage(self):
    pass

  def get_storageinfo(self):
    pass
  
  def getluns(self):
    pass
  
  def cmd_reset(self):
    pass
