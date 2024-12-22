import re

from .exceptions import InstructionError
from .memory import Memory
from .mnemonic import MNEMONIC


def format_line(addr, text, code):
    items = text.split(" ", maxsplit=2)
    return f"{items[0]:8}{' '.join(items[1:]):32};[{addr:04x}] " + " ".join(
        [f"{c:02x}" for c in code]
    )


def disasm_line(mem):
    addr = mem.addr
    op = mem.next_byte()
    if op is None:
        return -1, ""
    try:
        func = MNEMONIC.get(op)
        text = func(op, mem)
        line = format_line(addr, text, mem[addr : mem.addr])
        return addr, line
    except InstructionError as e:
        raise InstructionError(f"{e} at {addr:04x}")


def disasm_nlines(mem, addr, max_line):
    if not mem.addr_in(addr):
        print(f"start address is out of range {addr:04x}")
        exit()

    mem.addr = addr
    op = mem.next_byte()
    lines = {}
    count = 0
    while op is not None:
        func = MNEMONIC.get(op)
        try:
            text = func(op, mem)
            line = format_line(addr, text, mem[addr : mem.addr])
            print(" " * 16 + line)
            lines[addr] = line
        except Exception as e:
            print(e, f"at {addr:04x}")
            return lines

        lines[addr] = format_line(addr, text, mem[addr : mem.addr])
        addr = mem.addr
        op = mem.next_byte()
        count += 1
        if count >= max_line:
            break
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
    disasm_nlines(mem)
