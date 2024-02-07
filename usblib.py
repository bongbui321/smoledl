import array
import time
import sys

import usb.core
import usb.util
import usb.backend.libusb0
import usb.backend.libusb1
from ctypes import c_void_p, c_int

class usb_class:
  def __init__(self, portconfig=None, serial_number=None):
    # Deviceclass
    self.connected = False
    self.portconfig = portconfig
    self.timeout = 1000
    self.maxsize = 512
    self.vid = None
    self.pid = None
    self.serial_number = serial_number
    #self.configuration = None
    self.device = None
    self.devclass = -1

    self.EP_IN = None
    self.EP_OUT = None
    self.is_serial = False
    self.buffer = array.array('B', [0]) * 1048576
    if sys.platform.startswith('freebsd') or sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
      self.backend = usb.backend.libusb1.get_backend(find_library=lambda x: "libusb-1.0.so")
    else:
      print("Only support Unix-based machine")
      sys.exit(1)
    if self.backend is not None:
      try:
        self.backend.lib.libusb_set_option.argtypes = [c_void_p, c_int]
        self.backend.lib.libusb_set_option(self.backend.ctx, 1)
      except:
        self.backend = None

  def connect(self, EP_IN=-1, EP_OUT=-1):
    if self.connected:
      self.close()
      self.connected = False
    self.device = None
    self.EP_OUT = None
    self.EP_IN = None
    devices = usb.core.find(find_all=True, backend=self.backend)
    for d in devices:
      for usbid in self.portconfig:
        if d.idProduct == usbid[1] and d.idVendor == usbid[0]:
          #if self.serial_number is not None:
          #  if d.serial_number != self.serial_number:
          #    continue
          self.device = d
          self.vid = d.idVendor
          self.pid = d.idProduct
          self.serial_number = d.serial_number
          #print(self.serial_number)
          self.interface = usbid[2]
          break
      if self.device is not None:
        break

    if self.device is None:
      print("Couldn't detect the device. Is it connected ?")
      return False

    try:
      self.configuration = self.device.get_active_configuration()
    except usb.core.USBError as e:
      if e.strerror == "Configuration not set":
        self.device.set_configuration()
        self.configuration = self.device.get_active_configuration()
      if e.errno == 13:
        self.backend = usb.backend.libusb0.get_backend()
        self.device = usb.core.find(idVendor=self.vid, idProduct=self.pid, backend=self.backend)
    if self.configuration is None:
      print("Couldn't get device configuration.")
      return False
    if self.interface > self.configuration.bNumInterfaces:
      print("Invalid interface, max number is %d" % self.configuration.bNumInterfaces)
      return False
    count = 0
    for itf in self.configuration:
      print(count)
      count += 1 
      if self.devclass == -1:
        print("GET IN DEVCLass = -1")
        self.devclass = 0xFF
      if itf.bInterfaceClass == self.devclass:
        if self.interface == -1 or self.interface == itf.bInterfaceNumber:
          self.interface = itf
          self.EP_OUT = EP_OUT
          self.EP_IN = EP_IN
          for ep in itf:
            edir = usb.util.endpoint_direction(ep.bEndpointAddress)
            if (edir == usb.util.ENDPOINT_OUT and EP_OUT == -1) or ep.bEndpointAddress == (EP_OUT & 0xF):
              print("++++++++++++GOES IN EP_OUT SET")
              self.EP_OUT = ep
            elif (edir == usb.util.ENDPOINT_IN and EP_IN == -1) or ep.bEndpointAddress == (EP_OUT & 0xF):
              print("++++++++++++GOES IN EP_IN SET")
              self.EP_IN = ep
          break

    if self.EP_OUT is not None and self.EP_IN is not None:
      self.maxsize = self.EP_IN.wMaxPacketSize
      try:
        if self.device.is_kernel_driver_active(0):
          print("Detaching kernel driver")
          self.device.detach_kernel_driver(0)
      except Exception as err:
        print("No kernel driver supported: " + str(err))
      try:
        usb.util.claim_interface(self.device, 0)
      except:
        pass
      self.connected = True
      return True
    print("Couldn't find CDC interface. Aborting.")
    self.connected = False
    return False

  def close(self, reset=False):
    if self.connected:
      try:
        if reset:
          self.device.reset()
        if not self.device.is_kernel_driver_active(self.interface):
          # self.device.attach_kernel_driver(self.interface) #Do NOT uncomment
          self.device.attach_kernel_driver(0)
      except Exception as err:
        self.debug(str(err))
        pass
      usb.util.dispose_resources(self.device)
      del self.device
      if reset:
        time.sleep(2)
      self.connected = False
    
  def write(self, command, pktsize=None):
    if pktsize is None:
      pktsize = self.EP_OUT.wMaxPacketSize
    if isinstance(command, str):
      command = bytes(command, 'utf-8')
    pos = 0
    if command == b'':
      try:
        self.EP_OUT.write(b'')
      except usb.core.USBError as err:
        error = str(err.strerror)
        if "timeout" in error:
          try:
            self.EP_OUT.write(b'')
          except Exception as err:
            print(str(err))
            return False
        return True
    else:
      i = 0
      while pos < len(command):
        try:
          ctr = self.EP_OUT.write(command[pos:pos + pktsize])
          if ctr <= 0:
            print(ctr)
          pos += pktsize
        except Exception as err:
          print(str(err))
          i += 1
          if i == 3:
            return False
          pass
    return True
  
  def read(self, length=None, timeout=-1):
    if timeout == -1:
      timeout = self.timeout
    if length is None:
      length = self.maxsize
    return self.usbread(length, timeout)

  def usbread(self, resplen=None, timeout=0):
    if timeout == 0:
      timeout = 1
    if resplen is None:
      resplen = self.maxsize
    if resplen <= 0:
      print("Warning resplen <= 0!")
    res = bytearray()
    buffer = self.buffer[:resplen]
    epr = self.EP_IN.read
    extend = res.extend
    while len(res) < resplen:
      try:
        resplen=epr(buffer,timeout)
        extend(buffer[:resplen])
        if resplen == self.EP_IN.wMaxPacketSize:
          break
      except usb.core.USBError as e:
        error = str(e.strerror)
        if "timed out" in error:
          if timeout is None:
            return b""
          print("Timed out")
          if timeout == 10:
            return b""
          timeout += 1
          pass
        elif "Overflow" in error:
          self.error("USB Overflow")
          return b""
        else:
          print(repr(e))
          return b""
    return res[:resplen]
  
  def flush(self):
    return
