from io import BytesIO

def getint(valuestr):
  try:
    return int(valuestr)
  except:
    try:
      return int(valuestr, 16)
    except:
      return 0

class structhelper_io:
  pos = 0

  def __init__(self, data:BytesIO = None, direction='little'):
    self.data = data
    self.direction = direction
  
  def dword(self):
    dat = int.from_bytes(self.data.read(4), self.direction)
    return dat
  
  def qword(self):
    dat = int.from_bytes(self.data.read(8), self.direction)
    return dat

