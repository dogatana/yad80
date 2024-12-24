import os.path
import struct

from .memory import Memory


def read_file(file):
    with open(file, "rb") as fp:
        return fp.read()


def load_mzt(file):
    data = read_file(file)
    if data[0] != 1:
        print(f"invalid MZT file: {file}, : Attribute is ${data[0]:02X}")
        exit()
    size, offset, start = struct.unpack("<3H", data[0x12:0x18])
    if size + 128 != len(data):
        print(f"invalid MZT file: {file}, may be multiple data block")
        exit()

    return Memory(data[128 : size + 128], offset=offset, start=start)


def load_bin(file, offset):
    data = read_file(file)
    return Memory(data, offset=offset)


def load(file, offset):
    _, ext = os.path.splitext(file)
    ext = ext.lower()
    if ext == ".mzt":
        return load_mzt(file)
    else:
        return load_bin(file, offset)
