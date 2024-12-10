import os.path
import struct
from memory import Memory

def read_file(file):
    with open(file, "rb") as fp:
        return fp.read()

def load_mzt(file):
    data = read_file(file)
    offset, start = struct.unpack("<2H", data[0x14:0x18])
    return Memory(data[128:], offset=offset, start=start)
    
def load_bin(file):
    data = read_file(file)
    return Memory(data)

def load(file):
    _, ext = os.path.splitext(file)
    ext = ext.lower()
    if ext == ".mzt":
        return load_mzt(file)

        