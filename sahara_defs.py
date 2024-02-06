import sys
from io import BytesIO

from utils import structhelper_io

class DataError(Exception):
  pass

class cmd_t:
  SAHARA_HELLO_REQ = 0x1
  SAHARA_HELLO_RSP = 0x2
  SAHARA_READ_DATA = 0x3
  SAHARA_END_TRANSFER = 0x4
  SAHARA_DONE_REQ = 0x5
  SAHARA_DONE_RSP = 0x6
  #SAHARA_RESET_REQ = 0x7
  SAHARA_RESET_RSP = 0x8
  #SAHARA_MEMORY_DEBUG = 0x9
  #SAHARA_MEMORY_READ = 0xA
  SAHARA_CMD_READY = 0xB
  SAHARA_SWITCH_MODE = 0xC
  #SAHARA_EXECUTE_REQ = 0xD
  SAHARA_EXECUTE_RSP = 0xE
  #SAHARA_EXECUTE_DATA = 0xF
  #SAHARA_64BIT_MEMORY_DEBUG = 0x10
  #SAHARA_64BIT_MEMORY_READ = 0x11
  SAHARA_64BIT_MEMORY_READ_DATA = 0x12
  #SAHARA_RESET_STATE_MACHINE_ID = 0x13

class exec_cmd_t:
  #SAHARA_EXEC_CMD_NOP = 0x00
  SAHARA_EXEC_CMD_SERIAL_NUM_READ = 0x01
  SAHARA_EXEC_CMD_MSM_HW_ID_READ = 0x02
  SAHARA_EXEC_CMD_OEM_PK_HASH_READ = 0x03
  #SAHARA_EXEC_CMD_SWITCH_TO_DMSS_DLOAD = 0x04
  #SAHARA_EXEC_CMD_SWITCH_TO_STREAM_DLOAD = 0x05
  #SAHARA_EXEC_CMD_READ_DEBUG_DATA = 0x06
  #SAHARA_EXEC_CMD_GET_SOFTWARE_VERSION_SBL = 0x07
  #SAHARA_EXEC_CMD_GET_COMMAND_ID_LIST = 0x08
  #SAHARA_EXEC_CMD_GET_TRAINING_DATA = 0x09

class sahara_mode_t:
  SAHARA_MODE_IMAGE_TX_PENDING = 0x0
  #SAHARA_MODE_IMAGE_TX_COMPLETE = 0x1
  #SAHARA_MODE_MEMORY_DEBUG = 0x2
  SAHARA_MODE_COMMAND = 0x3

class status_t:
  SAHARA_STATUS_SUCCESS = 0x00  # Invalid command received in current state
  SAHARA_NAK_INVALID_CMD = 0x01  # Protocol mismatch between host and target
  SAHARA_NAK_PROTOCOL_MISMATCH = 0x02  # Invalid target protocol version
  SAHARA_NAK_INVALID_TARGET_PROTOCOL = 0x03  # Invalid host protocol version
  SAHARA_NAK_INVALID_HOST_PROTOCOL = 0x04  # Invalid packet size received
  SAHARA_NAK_INVALID_PACKET_SIZE = 0x05  # Unexpected image ID received
  SAHARA_NAK_UNEXPECTED_IMAGE_ID = 0x06  # Invalid image header size received
  SAHARA_NAK_INVALID_HEADER_SIZE = 0x07  # Invalid image data size received
  SAHARA_NAK_INVALID_DATA_SIZE = 0x08  # Invalid image type received
  SAHARA_NAK_INVALID_IMAGE_TYPE = 0x09  # Invalid tranmission length
  SAHARA_NAK_INVALID_TX_LENGTH = 0x0A  # Invalid reception length
  SAHARA_NAK_INVALID_RX_LENGTH = 0x0B  # General transmission or reception error
  SAHARA_NAK_GENERAL_TX_RX_ERROR = 0x0C  # Error while transmitting READ_DATA packet
  SAHARA_NAK_READ_DATA_ERROR = 0x0D  # Cannot receive specified number of program headers
  SAHARA_NAK_UNSUPPORTED_NUM_PHDRS = 0x0E  # Invalid data length received for program headers
  SAHARA_NAK_INVALID_PDHR_SIZE = 0x0F  # Multiple shared segments found in ELF image
  SAHARA_NAK_MULTIPLE_SHARED_SEG = 0x10  # Uninitialized program header location
  SAHARA_NAK_UNINIT_PHDR_LOC = 0x11  # Invalid destination address
  SAHARA_NAK_INVALID_DEST_ADDR = 0x12  # Invalid data size received in image header
  SAHARA_NAK_INVALID_IMG_HDR_DATA_SIZE = 0x13  # Invalid ELF header received
  SAHARA_NAK_INVALID_ELF_HDR = 0x14  # Unknown host error received in HELLO_RESP
  SAHARA_NAK_UNKNOWN_HOST_ERROR = 0x15  # Timeout while receiving data
  SAHARA_NAK_TIMEOUT_RX = 0x16  # Timeout while transmitting data
  SAHARA_NAK_TIMEOUT_TX = 0x17  # Invalid mode received from host
  SAHARA_NAK_INVALID_HOST_MODE = 0x18  # Invalid memory read access
  SAHARA_NAK_INVALID_MEMORY_READ = 0x19  # Host cannot handle read data size requested
  SAHARA_NAK_INVALID_DATA_SIZE_REQUEST = 0x1A  # Memory debug not supported
  SAHARA_NAK_MEMORY_DEBUG_NOT_SUPPORTED = 0x1B  # Invalid mode switch
  SAHARA_NAK_INVALID_MODE_SWITCH = 0x1C  # Failed to execute command
  SAHARA_NAK_CMD_EXEC_FAILURE = 0x1D  # Invalid parameter passed to command execution
  SAHARA_NAK_EXEC_CMD_INVALID_PARAM = 0x1E  # Unsupported client command received
  SAHARA_NAK_EXEC_CMD_UNSUPPORTED = 0x1F  # Invalid client command received for data response
  SAHARA_NAK_EXEC_DATA_INVALID_CLIENT_CMD = 0x20  # Failed to authenticate hash table
  SAHARA_NAK_HASH_TABLE_AUTH_FAILURE = 0x21  # Failed to verify hash for a given segment of ELF image
  SAHARA_NAK_HASH_VERIFICATION_FAILURE = 0x22  # Failed to find hash table in ELF image
  SAHARA_NAK_HASH_TABLE_NOT_FOUND = 0x23  # Target failed to initialize
  SAHARA_NAK_TARGET_INIT_FAILURE = 0x24  # Failed to authenticate generic image
  SAHARA_NAK_IMAGE_AUTH_FAILURE = 0x25  # Invalid ELF hash table size.  Too bit or small.
  SAHARA_NAK_INVALID_IMG_HASH_TABLE_SIZE = 0x26
  SAHARA_NAK_ENUMERATION_FAILURE = 0x27
  SAHARA_NAK_HW_BULK_TRANSFER_ERROR = 0x28
  SAHARA_NAK_MAX_CODE = 0x7FFFFFFF  # To ensure 32-bits wide */

class CommandHandler:
  def pkt_hello_req(self, data):
    if len(data) < 0xC * 0x4:
      print("DataError!")
      sys.exit(1)
    st = structhelper_io(BytesIO(data))

    class req:
      cmd = st.dword()
      len = st.dword()
      version = st.dword()
      version_supported = st.dword()
      cmd_packet_length = st.dword()
      mode = st.dword()
      reserved1 = st.dword()
      reserved2 = st.dword()
      reserved3 = st.dword()
      reserved4 = st.dword()
      reserved5 = st.dword()
      reserved6 = st.dword()

    return req

  def pkt_cmd_hdr(self, data):
    if len(data)<2*4:
      print("DataError!")
      sys.exit(1)
    st = structhelper_io(BytesIO(data))
    class req:
      cmd = st.dword()
      len = st.dword()
    return req

  def pkt_image_end(self, data):
    if len(data)<0x4 * 0x4:
      raise DataError
    st = structhelper_io(BytesIO(data))
    class req:
      cmd = st.dword()
      len = st.dword()
      image_id = st.dword()
      image_tx_status = st.dword()
    return req

  def pkt_done(self, data):
    if len(data)<0x3 * 4:
      raise DataError
    st = structhelper_io(BytesIO(data))
    class req:
      cmd = st.dword()
      len = st.dword()
      image_tx_status = st.dword()
    return req

  # TODO: other pkt methods
