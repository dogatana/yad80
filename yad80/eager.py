from .disasm import disasm_line
from collections import defaultdict
from dataclasses import dataclass
import re

debug = False

@dataclass
class Label:
    addr: int
    label_type: set
    used_addr: set
    processed: bool
    name_cache: str = ""

    @property
    def name(self):
        if self.name_cache != "":
            return self.name_cache

        base = "".join(sorted(self.label_type))
        self.name_cache = f"{base}_{self.addr:04X}"
        return self.name_cache

    def check_external(self, mem):
        if mem.addr_in(self.addr):
            return
        if not self.name.startswith("EX_"):
            self.name_cache = "EX_" + self.name_cache


def add_branch_label(labels, addr, line):
    LABEL_TYPE = {"CALL": "CD", "JR": "JR", "JP": "JP", "DJNZ": "JR"}
    m = re.search(
        r"^\s*(JP|JR|DJNZ|CALL)\s+.*?\$([0-9a-f]{4})", line, flags=re.IGNORECASE
    )
    if m is None:
        return
    target = int(m.group(2), base=16)
    label = labels.setdefault(target, Label(target, set(), set(), False))
    label.label_type.add(LABEL_TYPE[m.group(1)])
    label.used_addr.add(addr)


def add_data_label(labels, addr, line):
    m = re.search(r"\(\$([0-9a-f]{4})\)", line, flags=re.IGNORECASE)
    if m is None:
        return
    target = int(m.group(1), base=16)
    label = labels.setdefault(target, Label(target, set(), set(), False))
    label.label_type.add("DT")
    label.used_addr.add(addr)


STOP = set(["RET", "RETI", "RETN", "HALT"])


def should_pause(line):
    code = line.split(";")[0].strip()
    if code in STOP:
        return True
    m = re.search(r"^\s*(JP|JR)\s+[\$(]", line)
    return m is not None


def in_range(ranges, addr):
    return any(addr in r for r in ranges)


def replace_branch_addr(labels, lines):
    for target, label in labels.items():
        for addr in label.used_addr:
            lines[addr] = lines[addr].replace(f"${target:04X}", label.name)


def replace_string_addr(labels, lines):
    addrs = set()
    for label in labels.values():
        if re.match(r"(EX_)?ST_", label.name) is not None:
            addrs.add(label.addr)

    for addr, line in lines.items():
        m = re.search(r"LD\s+\w{2},\$([0-9A-F]{4})", line)
        if m is None:
            continue
        str_addr = int(m.group(1), base=16)
        if str_addr not in addrs:
            continue
        lines[addr] = lines[addr].replace(f"${str_addr:04X}", labels[str_addr].name)


def bytes2ascii(bstr):
    block = bytearray(bstr)
    for n, b in enumerate(block):
        if b < 0x20 or b >= 0x7E:
            block[n] = ord(".")
    return block.decode("ascii")


def bytes2_string(bstr):
    ret = ""
    for b in bstr:
        if b < 0x20 or b >= 0x7E:
            ret += f"\\x{b:02x}"
        elif b == 0x22:
            ret += r"\""
        else:
            ret += chr(b)
    return ret


def merge_ranges(ranges):
    ranges.sort(key=lambda r: r.start)

    merged = True
    ofs = 0
    while merged:
        merged = False
        for n in range(ofs, len(ranges) - 1):
            if ranges[n].stop < ranges[n + 1].start:
                ofs += 1
                continue
            start = min(ranges[n].start, ranges[n + 1].start)
            stop = max(ranges[n].stop, ranges[n + 1].stop)
            ranges[n : n + 2] = [range(start, stop)]
            merged = True
            break

def define_db(mem, rng):
    lines = {}
    for addr in range(rng.start, rng.stop, 8):
        block = bytearray(mem[addr : min(addr + 8, rng.stop)])
        line = "DB    " + ",".join(f"${b:02X}" for b in block)
        line += "    " * (8 - len(block))
        for n, b in enumerate(block):
            if b < 0x20 or b >= 0x7E:
                block[n] = ord(".")
        line += f"   ;[{addr:04x}] " + block.decode("ascii")
        lines[addr] = line
    return lines


def disasm_eagerly(args, mem):
    global debug
    if args.debug:
        debug = True

    ranges = []
    lines = {}
    branch_labels = defaultdict(dict)
    data_labels = defaultdict(dict)

    # --code
    for rng in args.code:
        ranges.append(rng)
        mem.start = rng.start
        print(f"; start: {mem.start:04x}")
        while mem.addr < rng.stop:
            try:
                addr, line = disasm_line(mem)
                if line == "":
                    break
                lines[addr] = line
                add_branch_label(branch_labels, addr, line)
                add_data_label(data_labels, addr, line)
            except Exception as e:
                print(e)
                # exit()

    # --string
    for rng in args.string:
        ranges.append(rng)
        addr = rng.start
        text = bytes2_string(mem[addr : rng.stop])
        line = f'DB    "{text}" ;[{addr:04x}] {bytes2ascii(mem[addr:rng.stop])}'
        lines[addr] = line
        branch_labels[addr] = Label(addr, "ST", [], True)

    addrs = args.addr
    if not lines and not addrs:
        # no --code, no --addr
        addrs = [mem.min_addr]

    for start_addr in addrs:
        if start_addr in lines:
            continue
        start = mem.min_addr
        mem.start = start
        while True:
            try:
                addr, line = disasm_line(mem)
                if line == "":
                    break
                lines[addr] = line
                add_branch_label(branch_labels, addr, line)
                add_data_label(data_labels, addr, line)
            except Exception as e:
                print(e)
                exit()
            if should_pause(line):
                break
        ranges.append(range(start, mem.addr))

    while True:
        branches = sorted(a for a, lbl in branch_labels.items() if not lbl.processed)
        if not branches:
            break
        for start_addr in branches:
            if start_addr in lines or not mem.addr_in(start_addr):
                branch_labels[start_addr].processed = True
                continue

            mem.addr = start_addr
            while True:
                addr, line = disasm_line(mem)
                if line == "":
                    break
                lines[addr] = line
                add_branch_label(branch_labels, addr, line)
                add_data_label(data_labels, addr, line)
                if should_pause(line):
                    ranges.append(range(start_addr, mem.addr))
                    break

    if debug:
        breakpoint()
        
    # ranges.sort(key=lambda r: r.start)

    # merged = True
    # while merged:
    #     merged = False
    #     for n in range(len(ranges) - 1):
    #         if ranges[n].stop < ranges[n + 1].start:
    #             continue
    #         start = min(ranges[n].start, ranges[n + 1].start)
    #         stop = max(ranges[n].stop, ranges[n + 1].stop)
    #         ranges[n : n + 2] = [range(start, stop)]
    #         merged = True
    #         break
    merge_ranges(ranges)


    db_ranges = []
    min_start = ranges[0].start
    if min_start < mem.min_addr:
        db_ranges.append(range(mem.min_addr, min_start - 1))

    max_stop = max(r.stop for r in ranges)
    if max_stop <= mem.max_addr:
        db_ranges.append(range(max_stop, mem.max_addr + 1))

    for n, rng in enumerate(ranges[:-1]):
        db_ranges.append(range(rng.stop, ranges[n + 1].start))

    for rng in db_ranges:
        lines.update(define_db(mem, rng))

    for label in branch_labels.values():
        label.check_external(mem)
    replace_branch_addr(branch_labels, lines)
    replace_string_addr(branch_labels, lines)

    # external label - EX_ EQU
    for label in branch_labels.values():
        if not mem.addr_in(label.addr):
            print(f"{label.name:16}EQU   ${label.addr:04x}")
    print("")

    addrs = sorted(lines.keys())
    # ORG
    print(" " * 16 + f"ORG   ${addrs[0]:04X}\n")

    for addr in addrs:
        label = branch_labels.get(addr)
        if label is not None:
            print(f"\n{label.name}:")
        cols = lines[addr].split(";")
        print(" " * 16 + f"{cols[0].strip():40}; {cols[1].strip()}")

    # data or code
    print("")
    for rng in db_ranges:
        decoded = bytes2ascii(mem[rng.start : rng.stop])
        print(f"; ${rng.start:04x}-${rng.stop - 1:04x}, [${len(rng):3x}] ", end="")
        print(decoded[:32])
