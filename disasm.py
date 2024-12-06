from memory import Memory
import re
from exceptions import InstructionError
from mnemonic import MNEMONIC


def format_line(addr, text, code):
    items = text.split(" ", maxsplit=2)
    return f"{items[0]:6}{' '.join(items[1:]):34};[{addr:04x}] " + " ".join(
        [f"{c:02x}" for c in code]
    )

def disasm_one(mem):
    addr = mem.ofs
    op = mem.next_byte()
    if op is None:
        return -1, ""
    try:
        func = MNEMONIC.get(op)
        text = func(op, mem)
        line = format_line(addr, text, mem[addr : mem.ofs])
        return addr, line
    except InstructionError as e:
        raise InstructionError(f"{e} at {addr:04x}")


def disasm(mem):
    addr = mem.ofs
    op = mem.next_byte()
    lines = {}
    while op is not None:
        func = MNEMONIC.get(op)
        try:
            text = func(op, mem)
            line = format_line(addr, text, mem[addr : mem.ofs])
            print(line)
            lines[addr] = line
        except Exception as e:
            print(e, f"at {addr:04x}")
            exit()

        lines[addr] = format_line(addr, text, mem[addr : mem.ofs])
        addr = mem.ofs
        op = mem.next_byte()
    return lines


def get_branchs(lines):
    branches = {}
    for addr, text in lines.items():
        m = re.search(r"(?:JP|CALL|JR).*?\$([0-9A-F]{4})", text, flags=re.IGNORECASE)
        if m is None:
            continue
        branches[addr] = int(m.group(1), base=16)
    return branches


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        exit()
    mem = Memory(open(sys.argv[1], "rb").read())
    disasm(mem)