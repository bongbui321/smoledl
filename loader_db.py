import sys
import os
import inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    #from edlclient.Library.utils import read_object, print_progress, rmrf, LogBase
    from qualcomm_config import sochw, msmids #, root_cert_hash
except:
    #from Library.utils import read_object, print_progress, rmrf, LogBase
    from qualcomm_config import sochw, msmids, root_cert_hash

class loader_utils:
  def __init__(self):
    self.loaderdb = {}
  
  def init_loader_db(self):
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(current_dir, "Loaders")):
      for filename in filenames:
        fn = os.path.join(dirpath, filename)
        found = False
        for ext in [".bin", ".mbn", ".elf"]:
          if ext in filename[-4:]:
            found = True
            break
        if not found:
          continue
        try:
          hwid = filename.split("_")[0].lower()
          msmid = hwid[:8]
          try:
            int(msmid,16)
          except:
            continue
          devid = hwid[8:]
          if devid == '':
            continue
          if len(filename.split("_"))<2:
            continue
          pkhash = filename.split("_")[1].lower()
          for msmid in self.convertmsmid(msmid):
            mhwid = msmid + devid
            mhwid = mhwid.lower()
            if mhwid not in self.loaderdb:
              self.loaderdb[mhwid] = {}
            if pkhash not in self.loaderdb[mhwid]:
              self.loaderdb[mhwid][pkhash] = fn
        except Exception as e:  # pylint: disable=broad-except
          self.debug(f"Filename:{filename} => {str(e)}")
          continue
    return self.loaderdb

  def convertmsmid(self, msmid):
    msmiddb = []
    if int(msmid, 16) & 0xFF == 0xe1 or msmid == '00000000':
      return [msmid]
    socid = int(msmid, 16) >> 16
    if socid in sochw:
      names = sochw[socid].split(",")
      for name in names:
        for ids in msmids:
          if msmids[ids] == name:
            rmsmid = hex(ids)[2:].lower()
            while len(rmsmid) < 8:
              rmsmid = '0' + rmsmid
            msmiddb.append(rmsmid)
    return msmiddb
