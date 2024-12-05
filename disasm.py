from memory import Memory
import re
from exceptions import InstructionError

REG8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
REG16_SP = ["BC", "DE", "HL", "SP"]
REG16_AF = ["BC", "DE", "HL", "AF"]

ARITHMETIC = ["ADD", "ADC", "SUB", "SBC", "AND", "XOR", "OR", "CP"]
ROTATE_SHIFT = ["RLCA", "RRCA", "RLA", "RRA", "DAA", "CPL", "SCF", "CCF"]

ROTATE_SHIFT_R = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", None, "SRL"]
BIT_OP = [None, "BIT", "RES", "SET"]

CC = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]


def ld_reg8(op, _):
    r1 = (op >> 3) & 7
    r2 = op & 7
    return f"LD {REG8[r1]},{REG8[r2]}"


def ld_reg8_n(op, mem):
    r = (op >> 3) & 7
    n = mem.next_byte()
    return f"LD {REG8[r]},${n:02X}"


def ld_reg16_nn(op, mem):
    rr = (op >> 4) & 3
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD {REG16_SP[rr]},${n2:02X}{n1:02X}"


def ld_mem_HL(_, mem):
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD (${n2:02X}{n1:02X}),HL"


def ld_HL_mem(_, mem):
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD HL,(${n2:02X}{n1:02X})"


def ld_mem_A(_, mem):
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD (${n2:02X}{n1:02X}),A"


def ld_A_mem(_, mem):
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD A,(${n2:02X}{n1:02X})"


def arithmetic_reg8(op, _):
    p = (op >> 3) & 7
    r = op & 7
    return f"{ARITHMETIC[p]} {REG8[r]}"


def arithmetic_reg8_n(op, mem):
    p = (op >> 3) & 7
    n = mem.next_byte()
    return f"{ARITHMETIC[p]} ${n:02X}"


def add_hl(op, _):
    rr = (op >> 4) & 3
    return f"ADD HL,{REG16_SP[rr]}"


def inc_reg16(op, _):
    rr = (op >> 4) & 3
    return f"INC {REG16_SP[rr]}"


def dec_reg16(op, _):
    rr = (op >> 4) & 3
    return f"DEC {REG16_SP[rr]}"


def inc_reg8(op, _):
    r = (op >> 3) & 7
    return f"INC {REG8[r]}"


def dec_reg8(op, _):
    r = (op >> 3) & 7
    return f"DEC {REG8[r]}"


def rotate_shift(op, _):
    p = (op >> 3) & 7
    return ROTATE_SHIFT[p]


def djnz(_, mem):
    n = mem.next_byte()
    addr = mem.ofs + uint8_to_int8(n)
    return f"DJNZ ${addr:04X}"


def jr(_, mem):
    n = mem.next_byte()
    addr = mem.ofs + uint8_to_int8(n)
    return f"JR ${addr:04X}"


def jr_cc(op, mem):
    cc = (op >> 3) & 7 - 4
    n = mem.next_byte()
    addr = mem.ofs + uint8_to_int8(n)
    return f"JR {CC[cc]},${addr:04X}"


def ret_cc(op, _):
    cc = (op >> 3) & 7
    return f"RET {CC[cc]}"


def pop_reg16(op, _):
    rr = (op >> 4) & 3
    return f"POP {REG16_AF[rr]}"


def push_reg16(op, _):
    rr = (op >> 4) & 3
    return f"PUSH {REG16_AF[rr]}"


def jp_cc(op, mem):
    cc = (op >> 3) & 7
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"JP {CC[cc]},${n2:02X}{n1:02X}"


def jp(_, mem):
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"JP ${n2:02X}{n1:02X}"


def call_cc(op, mem):
    cc = (op >> 3) & 7
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"CALL {CC[cc]},${n2:02X}{n1:02X}"


def call(_, mem):
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"CALL ${n2:02X}{n1:02X}"


def rst(op, _):
    p = (op >> 3) & 7
    return f"RST ${p * 8:02X}"


def out(_, mem):
    n = mem.next_byte()
    return f"OUT (${n:02X}),A"


def in_(_, mem):
    n = mem.next_byte()
    return f"IN A,(${n:02X})"


def uint8_to_int8(value):
    if value <= 127:
        return value
    else:
        return value - 256


def opecode_cb(_, mem):
    op = mem.next_byte()
    return NMEMONIC_CB[op](op, mem)


def opecode_ed(_, mem):
    op = mem.next_byte()
    func = NMEMONIC_ED.get(op)
    if func is None:
        raise InstructionError(f"invalid instruction ed {op:02x}")
    return func(op, mem)


def opecode_dd_fd(op1, mem):
    op2 = mem.next_byte()
    # print(f"{op2:02x} ", end="")
    func = NMEMONIC_DD_FD.get(op2)
    if func is None:
        raise InstructionError(f"invalid instruction {op1:02x} {op2:02x}")
    return func(op1, op2, mem)


NMEMONIC = {
    0x00: lambda *_: "NOP",
    0x01: ld_reg16_nn,
    0x02: lambda *_: "LD (BC),A",
    0x03: inc_reg16,
    0x04: inc_reg8,
    0x05: dec_reg8,
    0x06: ld_reg8_n,
    0x07: rotate_shift,
    0x08: lambda *_: "EX AF,AF'",
    0x09: add_hl,
    0x0A: lambda *_: "LD A,(BC)",
    0x0B: dec_reg16,
    0x0C: dec_reg8,
    0x10: djnz,
    0x12: lambda *_: "LD (DE),A",
    0x18: jr,
    0x1A: lambda *_: "LD A,(DE)",
    0x20: jr_cc,
    0x22: ld_mem_HL,
    0x2A: ld_HL_mem,
    0x32: ld_mem_A,
    0x3A: ld_A_mem,
    0x40: ld_reg8,
    0x76: lambda *_: "HALT",
    0x80: arithmetic_reg8,
    0xC0: ret_cc,
    0xC1: pop_reg16,
    0xC2: jp_cc,
    0xC3: jp,
    0xC4: call_cc,
    0xC5: push_reg16,
    0xC6: arithmetic_reg8_n,
    0xC7: rst,
    0xC9: lambda *_: "RET",
    0xCB: opecode_cb,
    0xCD: call,
    0xD3: out,
    0xD9: lambda *_: "EXX",
    0xDB: in_,
    0xE3: lambda *_: "EX (SP),HL",
    0xE9: lambda *_: "JP (HL)",
    0xEB: lambda *_: "EX DE,HL",
    0xF3: lambda *_: "DI",
    0xF9: lambda *_: "LD SP,HL",
    0xFB: lambda *_: "EI",
    0xDD: opecode_dd_fd,
    0xED: opecode_ed,
    0xFD: opecode_dd_fd,
}


def rotate_shift_r(op, _):
    p = (op >> 3) & 7
    r = op & 7
    if ROTATE_SHIFT_R[p] is None:
        raise InstructionError(f"invalid instruction cb {op:02x}")
    return f"{ROTATE_SHIFT_R[p]} {REG8[r]}"


def bit_operation(op, _):
    bit_op = op >> 6
    n = (op >> 3) & 7
    r = op & 7
    return f"{BIT_OP[bit_op]} {n},{REG8[r]}"


NMEMONIC_CB = {
    0x00: rotate_shift_r,
    0x40: bit_operation,
}


def in_r(op, _):
    r = (op >> 3) & 7
    if r == 6:
        return "IN (C)"
    else:
        return f"IN {REG8[r]},(C)"


def out_r(op, _):
    r = (op >> 3) & 7
    if r == 6:
        return "OUT (C),0"
    else:
        return f"OUT (C),{REG8[r]}"


def sbc_hl(op, _):
    rr = (op >> 4) & 3
    return f"SBC HL,{REG16_SP[rr]}"


def adc_hl(op, _):
    rr = (op >> 4) & 3
    return f"ADC HL,{REG16_SP[rr]}"


def ld_mem_rr(op, mem):
    rr = (op >> 4) & 3
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD (${n2:02X}{n1:02X}),{REG16_SP[rr]}"


def ld_rr_mem(op, mem):
    rr = (op >> 4) & 3
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD {REG16_SP[rr]},(${n2:02X}{n1:02X})"


NMEMONIC_ED = {
    0x40: in_r,
    0x41: out_r,
    0x42: sbc_hl,
    0x4A: adc_hl,
    0x43: ld_mem_rr,
    0x53: ld_mem_rr,
    0x73: ld_mem_rr,
    0x4B: ld_rr_mem,
    0x5B: ld_rr_mem,
    0x7B: ld_rr_mem,
    0x47: lambda *_: "LD I,A",
    0x57: lambda *_: "LD A,I",
    0x4F: lambda *_: "LD R,A",
    0x5F: lambda *_: "LD A,R",
    0xA0: lambda *_: "LDI",
    0xA8: lambda *_: "LDD",
    0xB0: lambda *_: "LDIR",
    0xB8: lambda *_: "LDDR",
    0xA1: lambda *_: "CPI",
    0xA9: lambda *_: "CPD",
    0xB1: lambda *_: "CPIR",
    0xB9: lambda *_: "CPDR",
    0xA2: lambda *_: "INI",
    0xAA: lambda *_: "IND",
    0xB2: lambda *_: "INIR",
    0xBA: lambda *_: "INDR",
    0xA3: lambda *_: "OUTI",
    0xAB: lambda *_: "OUTD",
    0xB3: lambda *_: "OTIR",
    0xBB: lambda *_: "OTDR",
    0x44: lambda *_: "NEG",
    0x45: lambda *_: "RETN",
    0x4D: lambda *_: "RETI",
    0x46: lambda *_: "IM 0",
    0x56: lambda *_: "IM 1",
    0x5E: lambda *_: "IM 2",
    0x67: lambda *_: "RRD",
    0x6F: lambda *_: "RLD",
}


def add_reg16(op1, op2, _):
    ixy = "IX" if op1 == 0xDD else "IY"
    rr = (op2 >> 4) & 3
    src = ixy if rr == 2 else REG16_SP[rr]
    return f"ADD {ixy},{src}"


def ld_reg8_indexed(op1, op2, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    ofs = uint8_to_int8(mem.next_byte())
    sign = "-" if ofs < 0 else "+"
    r = (op2 >> 3) & 7
    if r == 6:
        raise InstructionError(f"invalid instruction {op1:02x} {op2:02x}")
    return f"LD {REG8[r]},({ixy}{sign}${abs(ofs):02X})"


def ld_indexed_reg8(op1, op2, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    ofs = uint8_to_int8(mem.next_byte())
    sign = "-" if ofs < 0 else "+"
    r = op2 & 7
    return f"LD ({ixy}{sign}${abs(ofs):02x}),{REG8[r]}"


def ld_index_n(op1, _, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD {ixy},${n2:02X}{n1:02X}"


def ld_mem_index(op1, _, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD (${n2:02X}{n1:02X}),{ixy}"


def ld_index_mem(op1, _, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    n1 = mem.next_byte()
    n2 = mem.next_byte()
    return f"LD {ixy},(${n2:02X}{n1:02X})"


def ld_indexed_n(op1, _, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    ofs = uint8_to_int8(mem.next_byte())
    sign = "-" if ofs < 0 else "+"
    n = mem.next_byte()
    return f"LD ({ixy}{sign}${abs(ofs):02X}),${n:02X}"


def inc_dec_indexed(op1, op2, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    incdec = "INC" if op2 == 0x34 else "DEC"
    ofs = uint8_to_int8(mem.next_byte())
    sign = "-" if ofs < 0 else "+"
    return f"{incdec} ({ixy}{sign}${abs(ofs):02X})"


def bit_shift(op1, _, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    n = mem.next_byte()
    ofs = uint8_to_int8(n)
    sign = "-" if ofs < 0 else "+"
    op2 = mem.next_byte()
    r = op2 & 7
    if r != 6:
        raise InstructionError(f"invalid instruction {op1:02x} cb {n:02x} {op2:02x}")
    mask = (op2 >> 6) & 3
    if mask == 0:
        shift_op = (op2 >> 3) & 7
        return f"{ROTATE_SHIFT_R[shift_op]} ({ixy}{sign}${abs(ofs):02X})"
    else:
        bit_op = (op2 >> 6) & 7
        n = (op2 >> 3) & 7
        return f"{BIT_OP[bit_op]} {n},({ixy}{sign}${abs(ofs):02X})"


NMEMONIC_DD_FD = {
    0x09: add_reg16,
    0x21: ld_index_n,
    0x22: ld_mem_index,
    0x2A: ld_index_mem,
    0x34: inc_dec_indexed,
    0x35: inc_dec_indexed,
    0x36: ld_indexed_n,
    0x23: lambda op, *_: "INC IX" if op == 0xDD else "INC IY",
    0x2B: lambda op, *_: "DEC IX" if op == 0xDD else "DEC IY",
    0x46: ld_reg8_indexed,
    0x70: ld_indexed_reg8,
    0xE1: lambda op, *_: "POP IX" if op == 0xDD else "POP IY",
    0xE5: lambda op, *_: "PUSH IX" if op == 0xDD else "PUSH IY",
    0xE3: lambda op, *_: "EX (SP),IX" if op == 0xDD else "EX (SP),IY",
    0xE9: lambda op, *_: "JP (IX)" if op == 0xDD else "JP (IY)",
    0xF9: lambda op, *_: "LD SP,IX" if op == 0xDD else "LD SP,IY",
    0xCB: bit_shift,
}


def init_dis():
    # LD r,r'
    for op in range(0x41, 0x80):
        if op == 0x76:  # HALT
            continue
        NMEMONIC[op] = NMEMONIC[0x40]

    # 8 bit arithmetic
    for op in range(0x81, 0xC0):
        NMEMONIC[op] = NMEMONIC[0x80]

    # INC rr, DEC rr
    for n in range(1, len(REG16_SP)):
        NMEMONIC[0x01 + n * 0x10] = NMEMONIC[0x01]  # LD rr,nn
        NMEMONIC[0x03 + n * 0x10] = NMEMONIC[0x03]  # INC rr
        NMEMONIC[0x09 + n * 0x10] = NMEMONIC[0x09]  # ADD HL,rr
        NMEMONIC[0x0B + n * 0x10] = NMEMONIC[0x0B]  # DEC rr

    # INC r, DEC r # LD r,n
    for n in range(1, len(REG8)):
        NMEMONIC[0x04 + n * 8] = NMEMONIC[0x04]  # INC r
        NMEMONIC[0x05 + n * 8] = NMEMONIC[0x05]  # DEC r
        NMEMONIC[0x06 + n * 8] = NMEMONIC[0x06]  # LD  r, n

    # Rotate and Shift
    for n in range(1, len(ROTATE_SHIFT)):
        NMEMONIC[0x07 + n * 8] = NMEMONIC[0x07]

    # JR cc
    for n in range(1, 4):
        NMEMONIC[0x20 + n * 8] = NMEMONIC[0x20]

    # call cc
    for n in range(1, len(CC)):
        NMEMONIC[0xC4 + n * 8] = NMEMONIC[0xC4]  # CALL CC
        NMEMONIC[0xC2 + n * 8] = NMEMONIC[0xC2]  # JP CC,nnnn

    # RET cc
    for n in range(1, len(CC)):
        NMEMONIC[0xC0 + n * 8] = NMEMONIC[0xC0]

    # PUSH rr, POP rr
    for n in range(1, len(REG16_AF)):
        NMEMONIC[0xC1 + n * 0x10] = NMEMONIC[0xC1]  # PUSH rr
        NMEMONIC[0xC5 + n * 0x10] = NMEMONIC[0xC5]  # PUSH rr

    # 8 bit arithmetic
    for n in range(1, len(ARITHMETIC)):
        NMEMONIC[0xC6 + n * 8] = NMEMONIC[0xC6]

    # RST
    for n in range(1, 8):
        NMEMONIC[0xC7 + n * 8] = NMEMONIC[0xC7]

    # CB
    for n in range(1, 0x40):
        NMEMONIC_CB[n] = NMEMONIC_CB[0]  # rotate r, shift r
    for n in range(0x41, 0x100):
        NMEMONIC_CB[n] = NMEMONIC_CB[0x40]  # bit operation

    # ED
    for n in range(1, 8):
        NMEMONIC_ED[0x40 + n * 8] = NMEMONIC_ED[0x40]  # IN r,(C)
        NMEMONIC_ED[0x41 + n * 8] = NMEMONIC_ED[0x41]  # OUT (C),r

    for n in range(1, len(REG16_SP)):
        NMEMONIC_ED[0x42 + n * 0x10] = NMEMONIC_ED[0x42]
        NMEMONIC_ED[0x4A + n * 0x10] = NMEMONIC_ED[0x4A]

    # DD, FD
    for n in range(1, 4):
        NMEMONIC_DD_FD[0x09 + n * 0x10] = NMEMONIC_DD_FD[0x09]  # LD ixy,REG16

    for n in range(1, len(REG8)):
        NMEMONIC_DD_FD[0x46 + n * 8] = NMEMONIC_DD_FD[0x46]  # LD r,(ixy+n)
        NMEMONIC_DD_FD[0x70 + n] = NMEMONIC_DD_FD[0x70]  # LD r,(ixy+n)

    # for n in range(len(ROTATE_SHIFT_R)):
    #     NMEMONIC_DD_FD[0x06 + n * 8] = bit_shift  # shift rotate

    # for op in BIT_OP:
    #     for n in range(8):
    #         NMEMONIC_DD_FD[0x46 + n * 8] = bit_shift # bit


def format_line(addr, text, code):
    items = text.split(" ", maxsplit=2)
    return f"{items[0]:6}{' '.join(items[1:]):34};[{addr:04x}] " + " ".join(
        [f"{c:02x}" for c in code]
    )


init_dis()


def disasm(mem):
    op = mem.next_byte()
    addr = mem.ofs
    lines = {}
    while op is not None:
        func = NMEMONIC.get(op)
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
    lines = disasm(mem)
    for text in lines.values():
        print(text)

    exit()
    branches = get_branchs(lines)
    for addr, branch in branches.items():
        print(f"{addr:04x}->{branch:04x}", lines[addr])