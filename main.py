import argparse

import disasm
from eager import disasm_eagerly
from memory import Memory


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


def parse_range(arg):
    addrs = arg.split("-")
    if len(addrs) != 2:
        raise argparse.ArgumentTypeError
    start = parse_addr(addrs[0])
    stop = parse_addr(addrs[1]) + 1
    if start >= stop:
        raise argparse.ArgumentTypeError
    return range(start, stop)


def parse_args(args):
    parser = argparse.ArgumentParser(prog="yad80")
    parser.add_argument(
        "--data",
        "-d",
        action="extend",
        nargs="*",
        type=parse_range,
        default=[],
        help="disasm as data",
    )
    parser.add_argument(
        "--code",
        "-c",
        action="extend",
        nargs="*",
        type=parse_range,
        default=[],
        help="disasm as code",
    )
    parser.add_argument(
        "--string",
        "-s",
        action="extend",
        nargs="*",
        type=parse_range,
        default=[],
        help="address(es) to disasm",
    )
    parser.add_argument(
        "--addr",
        "-a",
        action="extend",
        nargs="*",
        type=parse_addr,
        default=[],
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
    mem = Memory(open(args.FILE, "rb").read(), offset=args.offset)

    if args.eager:
        disasm_eagerly(args, mem)
        exit()

    if not args.addr:
        start_addr = mem.addr
    elif len(args.addr) == 1:
        start_addr = args.addr[0]
    else:
        print(f"mulitple address {args.addr} specified")
        exit()

    disasm.disasm(mem, start_addr, args.lines)
