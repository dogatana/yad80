from exceptions import InstructionError
from mnemonic_cb import MNEMONIC_CB
from mnemonic_ed import MNEMONIC_ED
from mnemonic_dd_fd import MNEMONIC_DD_FD

REG8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
REG16_SP = ["BC", "DE", "HL", "SP"]
REG16_AF = ["BC", "DE", "HL", "AF"]

ARITHMETIC = ["ADD", "ADC", "SUB", "SBC", "AND", "XOR", "OR", "CP"]
ROTATE_SHIFT = ["RLCA", "RRCA", "RLA", "RRA", "DAA", "CPL", "SCF", "CCF"]

ROTATE_SHIFT_R = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", None, "SRL"]
BIT_OP = [None, "BIT", "RES", "SET"]

CC = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]


def ld_reg8_reg8(op, _):
    r1 = (op >> 3) & 7
    r2 = op & 7
    if r1 == r2 == 6: # just in case
        return "HALT"
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
    return MNEMONIC_CB[op](op, mem)


def opecode_ed(_, mem):
    op = mem.next_byte()
    func = MNEMONIC_ED.get(op)
    if func is None:
        raise InstructionError(f"invalid instruction ed {op:02x}")
    return func(op, mem)


def opecode_dd_fd(op1, mem):
    op2 = mem.next_byte()
    # print(f"{op2:02x} ", end="")
    func = MNEMONIC_DD_FD.get(op2)
    if func is None:
        raise InstructionError(f"invalid instruction {op1:02x} {op2:02x}")
    return func(op1, op2, mem)


MNEMONIC = {
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
    0x0a: lambda *_: "LD A,(BC)",
    0x0b: dec_reg16,
    0x0c: dec_reg8,
    0x10: djnz,
    0x12: lambda *_: "LD (DE),A",
    0x18: jr,
    0x1a: lambda *_: "LD A,(DE)",
    0x20: jr_cc,
    0x22: ld_mem_HL,
    0x2a: ld_HL_mem,
    0x32: ld_mem_A,
    0x3a: ld_A_mem,
    0x40: ld_reg8_reg8,
    0x76: lambda *_: "HALT",
    0x80: arithmetic_reg8,
    0xc0: ret_cc,
    0xc1: pop_reg16,
    0xc2: jp_cc,
    0xc3: jp,
    0xc4: call_cc,
    0xc5: push_reg16,
    0xc6: arithmetic_reg8_n,
    0xc7: rst,
    0xc9: lambda *_: "RET",
    0xcb: opecode_cb,
    0xcd: call,
    0xd3: out,
    0xd9: lambda *_: "EXX",
    0xdb: in_,
    0xe3: lambda *_: "EX (SP),HL",
    0xe9: lambda *_: "JP (HL)",
    0xeb: lambda *_: "EX DE,HL",
    0xf3: lambda *_: "DI",
    0xf9: lambda *_: "LD SP,HL",
    0xfb: lambda *_: "EI",
    0xdd: opecode_dd_fd,
    0xed: opecode_ed,
    0xfd: opecode_dd_fd,
}

def init_instruction_dict():
    for op in range(0x41, 0x80):
        if op == 0x76:  # HALT
            continue
        MNEMONIC[op] = MNEMONIC[0x40] # LD r,r'   

    for op in range(0x81, 0xc0):
        MNEMONIC[op] = MNEMONIC[0x80] # 8 bit arithmetic

    for n in range(1, len(REG16_SP)):
        MNEMONIC[0x01 + n * 0x10] = MNEMONIC[0x01]  # LD rr,nn
        MNEMONIC[0x03 + n * 0x10] = MNEMONIC[0x03]  # INC rr
        MNEMONIC[0x09 + n * 0x10] = MNEMONIC[0x09]  # ADD HL,rr
        MNEMONIC[0x0b + n * 0x10] = MNEMONIC[0x0b]  # DEC rr

    for n in range(1, len(REG8)):
        MNEMONIC[0x04 + n * 8] = MNEMONIC[0x04]  # INC r
        MNEMONIC[0x05 + n * 8] = MNEMONIC[0x05]  # DEC r
        MNEMONIC[0x06 + n * 8] = MNEMONIC[0x06]  # LD r,n

    for n in range(1, len(ROTATE_SHIFT)):
        MNEMONIC[0x07 + n * 8] = MNEMONIC[0x07]  # rotate and shift

    for n in range(1, 4):
        MNEMONIC[0x20 + n * 8] = MNEMONIC[0x20]  # JR cc

    for n in range(1, len(CC)):
        MNEMONIC[0xc0 + n * 8] = MNEMONIC[0xc0]  # RET cc
        MNEMONIC[0xc2 + n * 8] = MNEMONIC[0xc2]  # JP CC,nnnn
        MNEMONIC[0xc4 + n * 8] = MNEMONIC[0xc4]  # CALL CC

    for n in range(1, len(REG16_AF)):
        MNEMONIC[0xc1 + n * 0x10] = MNEMONIC[0xc1]  # POP rr
        MNEMONIC[0xc5 + n * 0x10] = MNEMONIC[0xc5]  # PUSH rr

    for n in range(1, len(ARITHMETIC)):
        MNEMONIC[0xc6 + n * 8] = MNEMONIC[0xc6] # 8 bit arithmetic

    for n in range(1, 8):
        MNEMONIC[0xc7 + n * 8] = MNEMONIC[0xc7]  # RST n

init_instruction_dict()