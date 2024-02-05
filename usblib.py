import usb.core
import usb.util
import usb.backend.libusb0
import usb.backend.libusb1
import array
import time
from ctypes import c_void_p, c_int

class usb_class:
  def __init__(self, portconfig=None):
    self.maxsize = 512
    self.timeout = 1000
    self.EP_IN = None
    self.EP_OUT = None
    self.buffer = array.array('B', [0]) * 1048576
    self.backend = usb.backend.libusb1.get_backend(find_library=lambda x: "libusb-1.0.so")
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
      devices = usb.core.find(find_all=True, backend=self.backend)
      for d in devices:
        for usbid in self.portconfig:
          if d.idProduct == usbid[1] and d.idVendor == usbid[0]:
            if self.serial_number is not None:
              if d.serial_number != self.serial_number:
                continue
            self.device = d
            self.vid = d.idVendor
            self.pid = d.idProduct
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
        self.error("Couldn't get device configuration.")
        return False
      if self.interface > self.configuration.bNumInterfaces:
        print("Invalid interface, max number is %d" % self.configuration.bNumInterfaces)
        return False
      for itf in self.configuration:
        if self.devclass == -1:
          self.devclass = 0xFF
        if itf.bInterfaceClass == self.devclass:
          if self.interface == -1 or self.interface == itf.bInterfaceNumber:
            self.interface = itf
            self.EP_OUT = EP_OUT
            self.EP_IN = EP_IN
            for ep in itf:
              edir = usb.util.endpoint_direction(ep.bEndpointAddress)
              if (edir == usb.util.ENDPOINT_OUT and EP_OUT == -1) or ep.bEndpointAddress == (EP_OUT & 0xF):
                self.EP_OUT = ep
              elif (edir == usb.util.ENDPOINT_IN and EP_IN == -1) or ep.bEndpointAddress == (EP_OUT & 0xF):
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
            self.debug(str(err))
            return False
        return True
    else:
      i = 0
      while pos < len(command):
        try:
          ctr = self.EP_OUT.write(command[pos:pos + pktsize])
          if ctr <= 0:
            self.info(ctr)
          pos += pktsize
        except Exception as err:
          self.debug(str(err))
          i += 1
          if i == 3:
            return False
          pass
    self.verify_data(bytearray(command), "TX:")
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
      self.info("Warning !")
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
