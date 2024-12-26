import re
from collections import defaultdict
from dataclasses import dataclass

from .disasm import disasm_line

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


def replace_branch_addr_ref(labels, lines):
    for target, label in labels.items():
        # if target not in lines:
        #     continue
        for addr in label.used_addr:
            lines[addr] = lines[addr].replace(f"${target:04X}", label.name)


def addr_label(addr, branch_labels, data_labels):
    if addr in branch_labels:
        return branch_labels[addr].name
    if addr in data_labels:
        return data_labels[addr].name


def bytes2ascii(bstr):
    block = bytearray(bstr)
    for n, b in enumerate(block):
        if b < 0x20 or b >= 0x7E:
            block[n] = ord(".")
    return block.decode("ascii")


def bytes2string(bstr):
    ret = ""
    in_str = False
    if 0x20 <= bstr[0] <= 0x7E:
        in_str = True
        ret += '"'
    for b in bstr:
        if 0x20 <= b <= 0x7E and in_str:
            c = chr(b) if b != 0x22 else r"\""
            ret += c
        elif 0x20 <= b <= 0x7E:
            in_str = True
            ret += '"'
            c = chr(b) if b != 0x22 else r"\""
            ret += c
        elif in_str:
            in_str = False
            ret += f'",${b:02X},'
        else:
            ret += f"${b:02X},"
    if in_str:
        return ret + '"'
    else:
        return ret[:-1]


def scan_str_ref(lines, branch_labels):
    target_addrs = set(
        addr for addr, lbl in branch_labels.items() if "ST" in lbl.label_type
    )
    for addr, line in lines.items():
        m = re.search(r"(\(?\$[0-9a-f]{4}\)?)", line, flags=re.IGNORECASE)
        if m is None:
            continue
        if m.group(1)[0] == "$":
            ref_addr = int(m.group(1)[1:], base=16)
        else:
            ref_addr = int(m.group(1)[2:6], base=16)
        if ref_addr not in target_addrs:
            continue
        branch_labels[ref_addr].used_addr.add(addr)


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


def create_data_ranges(code_ranges, min_addr, max_addr, label_addrs):
    data_ranges = []

    min_start = min(r.start for r in code_ranges)
    if min_addr < min_start:
        data_ranges.append(range(min_addr, min_start - 1))
    max_stop = max(r.stop for r in code_ranges)
    if max_stop <= max_addr:
        data_ranges.append(range(max_stop, max_addr + 1))

    for n, rng in enumerate(code_ranges[:-1]):
        data_ranges.append(range(rng.stop, code_ranges[n + 1].start))

    if debug:
        breakpoint()

    ret_ranges = []
    addr_set = set(label_addrs)
    for rng in data_ranges:
        if not addr_set:
            ret_ranges.append(rng)
            continue
        addrs = sorted(a for a in addr_set if a in rng)
        if not addrs:
            ret_ranges.append(rng)
            continue
        start = rng.start
        for addr in addrs:
            ret_ranges.append(range(start, addr))
            start = addr
        ret_ranges.append(range(start, rng.stop))
        addr_set -= set(addrs)

    return ret_ranges


def create_db_lines(lines, data_ranges, mem):
    for rng in data_ranges:
        lines.update(set_db_line(mem, rng))


def set_db_line(mem, rng):
    lines = {}
    for addr in range(rng.start, rng.stop, 8):
        block = bytearray(mem[addr : min(addr + 8, rng.stop)])
        line = "DB      " + ",".join(f"${b:02X}" for b in block)
        line += "    " * (8 - len(block))
        for n, b in enumerate(block):
            if b < 0x20 or b >= 0x7E:
                block[n] = ord(".")
        line += f"   ;[{addr:04x}] " + block.decode("ascii")
        lines[addr] = line
    return lines


def define_equ(mem, line_addrs, *group):
    for labels in group:
        for addr in sorted(labels.keys()):
            if not mem.addr_in(addr):
                print(f"{labels[addr].name:16}EQU     ${labels[addr].addr:04x}")
                continue
            if addr not in line_addrs:
                print(
                    f"{labels[addr].name:16}EQU     ${labels[addr].addr:04x} ; within CODE"
                )
                continue
    print("")


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
        mem.addr = rng.start
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
        text = bytes2string(mem[addr : rng.stop])
        line = f'DB    {text} ;[{addr:04x}] {" ".join(f"{b:02x}" for b in mem[addr:rng.stop])}'
        lines[addr] = line
        branch_labels[addr] = Label(addr, "ST", set(), True)

    # --addr
    addrs = args.addr
    if not lines and not addrs:
        # no --code, no --addr
        addrs = [mem.start]

    for start_addr in addrs:
        if start_addr in lines:
            continue
        mem.addr = start_addr
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
        ranges.append(range(start_addr, mem.addr))

    # branch addresses
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

    scan_str_ref(lines, branch_labels)
    merge_ranges(ranges)

    # DB
    data_ranges = create_data_ranges(
        ranges, mem.min_addr, mem.max_addr, sorted(data_labels.keys())
    )
    create_db_lines(lines, data_ranges, mem)

    # add EX_
    for labels in [branch_labels, data_labels]:
        for label in labels.values():
            label.check_external(mem)

    # add labels
    replace_branch_addr_ref(branch_labels, lines)
    replace_branch_addr_ref(data_labels, lines)

    # define external and in-code label with  EQU
    define_equ(mem, lines.keys(), branch_labels, data_labels)

    addrs = sorted(lines.keys())
    # ORG
    print(" " * 16 + f"ORG     ${addrs[0]:04X}\n")

    for addr in addrs:
        label = addr_label(addr, branch_labels, data_labels)
        if label is None:
            print(" " * 16, end="")
        elif len(label) < 15:
            label += ":"
            print(f"\n{label:16}", end="")
        else:
            print(f"\n{label}:")
        cols = lines[addr].split(";")
        print(f"{cols[0].strip():40}; {cols[1].strip()}")

    # data or code
    output_information(mem, branch_labels, data_labels, data_ranges)


def output_information(mem, branch_labels, data_labels, data_ranges):
    def print_xref(name, refs):
        ADDR_PER_LINE = 10
        for index in range(0, len(refs), ADDR_PER_LINE):
            print(f"; {name:16}", end="")
            print(
                " ".join(
                    f"${x:04x}"
                    for x in refs[index : min(index + ADDR_PER_LINE, len(refs))]
                )
            )
            name = ""

    print("\n; XREF information")
    for addr in sorted(list(branch_labels.keys() | data_labels.keys())):
        if addr in branch_labels:
            print_xref(branch_labels[addr].name, sorted(branch_labels[addr].used_addr))
        if addr in data_labels:
            print_xref(data_labels[addr].name, sorted(data_labels[addr].used_addr))

    print("\n; DATA summary")
    for rng in data_ranges:
        decoded = bytes2ascii(mem[rng.start : rng.stop])
        print(f"; ${rng.start:04x}-${rng.stop - 1:04x}, [${len(rng):4x}] ", end="")
        print(decoded[:48])
