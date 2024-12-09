import disasm
from collections import defaultdict
from dataclasses import dataclass
import re


@dataclass
class Label:
    addr: int
    label_type: set
    used_addr: set
    processed: bool
    name: str = ""


labels = defaultdict(dict)

LABEL_TYPE = {
    "CALL": "C",
    "JR": "R",
    "JP": "P",
}


def get_branch(addr, line):
    m = re.search(r"^\s*(JP|JR|CALL)\s+.*?\$([0-9a-f]{4})", line, flags=re.IGNORECASE)
    if m is None:
        return None
    target = int(m.group(2), base=16)
    label = labels.setdefault(target, Label(target, set(), set(), False))
    label.label_type.add(LABEL_TYPE[m.group(1)])
    label.used_addr.add(addr)
    return label


STOP = set(["RET", "RETI", "RETN", "HALT"])


def should_pause(line):
    code = line.split(";")[0].strip()
    if code in STOP:
        return True
    m = re.search(r"^\s*(JP|JR)\s+\$", line)
    return m is not None


def in_range(ranges, addr):
    return any(addr in r for r in ranges)


def set_label_name(mem):
    for label in labels.values():
        base = "".join(sorted(label.label_type))
        name = f"{base}_{label.addr:04X}"
        if mem.addr_in(label.addr):
            label.name = name
        else:
            label.name = f"EX_{name}"


def replace_addr(lines):
    for target, label in labels.items():
        for addr in label.used_addr:
            lines[addr] = lines[addr].replace(f"${target:04X}", label.name)


def disasm_eagerly(args, mem):
    ranges = []
    lines = {}

    for r in args.code:
        ranges.append(r)
        mem.start = r.start
        print(f"; start: {mem.start:04x}")
        while mem.addr < r.stop:
            try:
                addr, line = disasm.disasm_one(mem)
                if line == "":
                    break
                lines[addr] = line
                get_branch(addr, line)
            except Exception as e:
                print(e)
                exit()

    while True:
        branches = sorted(a for a, lbl in labels.items() if not lbl.processed)
        if not branches:
            break
        for start_addr in branches:
            if start_addr in lines or not mem.addr_in(start_addr):
                labels[start_addr].processed = True
                continue

            print(f"; start:{start_addr:04x}")
            mem.addr = start_addr
            while True:
                addr, line = disasm.disasm_one(mem)
                if line == "":
                    break
                lines[addr] = line
                get_branch(addr, line)
                if should_pause(line):
                    ranges.append(range(start_addr, mem.addr))
                    break

    ranges.sort(key=lambda r: r.start)
    # print(len(ranges))
    # for r in ranges:
    #     print(f"{r.start:04x}-{r.stop - 1:04x}", r)
    merged = True
    while merged:
        merged = False
        for n in range(len(ranges) - 1):
            if ranges[n].stop < ranges[n + 1].start:
                continue
            start = min(ranges[n].start, ranges[n + 1].start)
            stop = max(ranges[n + 1].stop, ranges[n + 1].stop)
            ranges[n : n + 2] = [range(start, stop)]
            merged = True
            break
    # print(len(ranges))
    # for r in ranges:
    #     print(f"{r.start:04x}-{r.stop - 1:04x}", r)

    # print("; db_ranges")
    db_ranges = []
    for n, r in enumerate(ranges[:-1]):
        db_ranges.append(range(r.stop, ranges[n + 1].start))

    for r in db_ranges:
        print(f"; {r.start:04x}-{r.stop - 1:04x}[{len(r)}]", r)
        for addr in range(r.start, r.stop, 8):
            block = bytearray(mem[addr : min(addr + 8, r.stop)])
            line = "db    " + ",".join(f"${b:02x}" for b in block)
            line += "    " * (8 - len(block))
            for n, b in enumerate(block):
                if b < 0x20 or b >= 0x7E:
                    block[n] = ord(".")
            line += f"   ;[{addr:04x}] " + block.decode("ascii")
            lines[addr] = line

    set_label_name(mem)
    replace_addr(lines)

    # EX_ EQU
    for label in labels.values():
        if label.name.startswith("EX_"):
            print(f"{label.name:16}EQU ${label.addr:04x}")
    print("")

    addrs = sorted(lines.keys())
    # ORG
    print(f"\t\tORG ${addrs[0]:04X}\n")

    for addr in addrs:
        label = labels.get(addr)
        if label is not None:
            print("")
            name = label.name + ":"
        else:
            name = ""
        print(f"{name:16}", end="")
        print(lines[addr])
