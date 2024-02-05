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

from edlclient.Library.firehose import firehose
try:
    from edlclient.Library.Modules.init import modules
except ImportError as e:
    pass

class firehose_client:
  def __init__(self, arguments, cdc, sahara):
    self.cdc = cdc
    self.sahara = sahara
    self.cfg = firehose.cfg()
    self.target_name = None
    self.connected = False
    # TODO: investigate what is needed
  
  def connect(self):
    pass
  
  def handle_firehose(self):
    pass
