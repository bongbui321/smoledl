from io import BytesIO

class structhelper_io:
  pos = 0

  def __init__(self, data:BytesIO = None, direction='little'):
    self.data = data
    self.diretion = direction
  
  def dword(self):
    dat = int.from_bytes(self.data.read(4), self.direction)
    return dat

