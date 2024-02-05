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
# cmd_info()
#   . enter_command_mode()
#   . cmdexec_get_msm_hwid()
#   . cmdexec_get_pkhash()
#   . cmd_modeswitch()
#
# cmdexec_get_serial_num()
#   . self.cmd_exec()
# 
# cmd_reset() - Not really important right now
# TODO: sahara_defs

from edlclient.Library.loader_db import loader_utils
from edlclient.Library.sahara_defs import ErrorDesc, cmd_t, exec_cmd_t, sahara_mode_t, status_t, \
    CommandHandler, SAHARA_VERSION

class sahara:
  def __init__(self, cdc):
    self.cdc = cdc
    self.version = 2.1
    self.hwid = None
    self.serial = None
    self.pkhash = None
    self.hwidstr = None
    self.ch = CommandHandler()
    self.loader_handler = loader_utils()
    self.loaderdb= self.loader_handler.init_loader_db()

  def connect(self):
    pass

  def cmd_info(self):
    pass

  def cmd_reset(self):
    pass

  def upload_loader(self):
    pass

  def enter_command_mode(self):
    pass
  
  def cmdexec_get_msm_hwid(self):
    pass

  def cmdexec_get_pkhash(self):
    pass

  def cmd_modeswitch(self):
    pass

  def cmd_hello(self):
    pass

  def get_rsp(self):
    pass

  def cmd_done(self):
    pass

  def get_error_desc(self):
    pass
