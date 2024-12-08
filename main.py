import re

import argparse

import disasm
from memory import Memory


def get_branch(line):
    m = re.search(r"^(?:JP|JR|CALL)\s+.*?\$([0-9a-f]{4})", line, flags=re.IGNORECASE)
    if m is None:
        return None
    return int(m.group(1), base=16)


STOP = set(["RET", "RETI", "RETN", "HALT"])


def should_pause(line):
    code = line.split(";")[0].strip()
    if code in STOP:
        return True
    m = re.search(r"^(JP|JR)\s+\$", line)
    return m is not None


def in_range(ranges, addr):
    return any(addr in r for r in ranges)


def parse_range(arg):
    addrs = arg.split("-")
    if len(addrs) != 2:
        raise argparse.ArgumentTypeError
    start = parse_addr(addrs[0])
    stop = parse_addr(addrs[1]) + 1
    if start >= stop:
        raise argparse.ArgumentTypeError
    return range(start, stop)


def parse_addr(arg):
    arg = arg.upper()
    if arg.startswith("$"):
        arg = arg[1:]
    if arg.endswith("H"):
        arg = arg[:-1]
    try:
        return int(arg, base=16)
    except:  # noqa:E722
        raise argparse.ArgumentTypeError(f"invalid address: {arg}")


def parse_args(args):
    parser = argparse.ArgumentParser(prog="yad80")
    parser.add_argument(
        "--data",
        "-d",
        action="extend",
        nargs="*",
        type=parse_range,
        help="disasm as data",
    )
    parser.add_argument(
        "--code",
        "-c",
        action="extend",
        nargs="*",
        type=parse_range,
        help="disasm as code",
    )
    parser.add_argument(
        "--string",
        "-s",
        action="extend",
        nargs="*",
        type=parse_range,
        help="address(es) to disasm",
    )
    parser.add_argument(
        "--addr",
        "-a",
        action="extend",
        nargs="*",
        type=parse_addr,
        help="address(es) to disasm",
    )
    parser.add_argument(
        "--eager", "-e", action="store_true", help="disasm yeagerly(default false)"
    )
    parser.add_argument(
        "--lines",
        "-l",
        type=int,
        default=10,
        help="max lines for output(default 10)",
    )
    parser.add_argument("--offset", "-o", type=int, default=0, help="address offset")
    parser.add_argument("FILE", help="file to disasm")

    return parser.parse_args(args)


if __name__ == "__main__":
    import sys

    args = parse_args(sys.argv[1:])
    print(args)

    mem = Memory(open(args.FILE, "rb").read(), offset=args.offset)

    if not args.eager:
        if args.addr is None:
            start_addr = mem.addr
        elif len(args.addr) == 1:
            start_addr = args.addr[0]
        else:
            print(f"mulitple address {sys.addr} specified")
            exit()

        disasm.disasm(mem, start_addr, args.lines)
        exit()

    branches = set()
    ranges = [range(0x4A)]
    lines = {}

    # 0000-0049
    # print("")
    print("; start: 0000")
    while True:
        try:
            addr, line = disasm.disasm_one(mem)
            if line == "":
                break
            lines[addr] = line
            branch = get_branch(line)
            if branch is not None and branch < mem.max_addr:
                branches.add(branch)
            if mem.addr >= 0x4A:
                break
        except Exception as e:
            print(e)
            exit()

    # 004a-0fff
    while branches:
        start_addr = min(branches)
        branches.remove(start_addr)
        if any(start_addr in r for r in ranges):
            continue

        # print("")
        print(f"; start:{start_addr:04x}")
        mem.addr = start_addr
        while True:
            addr, line = disasm.disasm_one(mem)
            if line == "":
                break
            lines[addr] = line
            branch = get_branch(line)
            if branch is not None and branch < mem.max_addr:
                branches.add(branch)
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

    for addr in sorted(lines.keys()):
        print(lines[addr])
