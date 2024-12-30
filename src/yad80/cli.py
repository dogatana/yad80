import argparse
import re
import sys
import traceback
from pathlib import Path

from .disasm import disasm_nlines
from .eager import disasm_eagerly
from .loader import load

DEFAULT_MAX_LINES = 32


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


def parse_option_file(file):
    if not Path(file).exists():
        raise argparse.ArgumentTypeError(f"'{file}' not found")

    options = []
    with open(file) as fp:
        for line in fp:
            line = re.sub(r"[#;].*$", "", line).strip()
            if not line:
                continue
            cols = line.split()
            if cols[0] not in {
                "--eager",
                "-e",
                "--code",
                "-c",
                "--string",
                "-s",
                "--addr",
                "-a",
                "--max-lines",
                "-m",
                "--offset",
                "-o",
            }:
                raise argparse.ArgumentTypeError(f"unrecognized option {cols[0]}")
            options.extend(cols)
        return options


def check_file(file):
    if not Path(file).exists():
        raise argparse.ArgumentTypeError(f"{file} not found")
    return file


def build_parser():
    parser = argparse.ArgumentParser(prog="yad80")
    parser.add_argument("--version", "-v", action="version", version="%(prog)s 0.1.6")
    parser.add_argument(
        "--option", nargs=1, type=parse_option_file, default=[], help="option file"
    )
    parser.add_argument(
        "--code",
        "-c",
        action="extend",
        nargs="*",
        type=parse_range,
        default=[],
        metavar="RANGE",
        help="address range(a1-a2) as code. a2 is an inclusive address",
    )
    parser.add_argument(
        "--string",
        "-s",
        action="extend",
        nargs="*",
        type=parse_range,
        default=[],
        metavar="RANGE",
        help="address range(a1-a2) as string. a2 is an inclusive address",
    )
    parser.add_argument(
        "--addr",
        "-a",
        action="extend",
        nargs="*",
        type=parse_addr,
        default=[],
        metavar="ADDR",
        help="address to disasm",
    )
    parser.add_argument(
        "--eager", "-e", action="store_true", help="disasm eagerly(default false)"
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help="debug flag(dev use)"
    )
    parser.add_argument(
        "--max-lines",
        "-m",
        type=int,
        default=DEFAULT_MAX_LINES,
        metavar="N",
        help=f"max lines to output(default {DEFAULT_MAX_LINES})",
    )
    parser.add_argument(
        "--offset",
        "-o",
        type=parse_addr,
        default=0,
        help="address offset for binary file",
    )
    parser.add_argument("FILE", type=check_file, help="file to disasm")

    return parser


def parse_args(args):
    parser = build_parser()
    parsed = parser.parse_args(args)
    if not parsed.option:
        return parsed

    base = parser.parse_args(parsed.option[0] + ["--", parsed.FILE])
    base.code.extend(parsed.code)
    base.string.extend(parsed.string)
    base.addr.extend(parsed.addr)
    base.eager = base.eager or parsed.eager
    if parsed.max_lines != DEFAULT_MAX_LINES:
        base.max_lines = parsed.max_lines
    if parsed.offset != 0:
        base.offset = parsed.offset

    return base


def cli_main(argv):
    args = parse_args(argv)

    mem = load(args.FILE, args.offset)

    if args.eager:
        try:
            disasm_eagerly(args, mem)
        except Exception as e:
            if args.debug:
                traceback.print_exception(e)
            else:
                print(f"Exception {e}")
        return

    if not args.addr:
        start_addr = mem.start
    elif len(args.addr) == 1:
        start_addr = args.addr[0]
    else:
        print(f"mulitple address {args.addr} specified")
        return

    disasm_nlines(mem, start_addr, args.max_lines)


def main():
    cli_main(sys.argv[1:])
