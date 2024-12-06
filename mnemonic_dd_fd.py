from exceptions import InstructionError
from mnemonic_defs import (
    REG8,
    REG16_SP,
    ARITHMETIC,
    ROTATE_SHIFT_R,
    BIT_OP,
    uint8_to_int8,
)



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


def arithmetic_indexed(op1, op2, mem):
    ixy = "IX" if op1 == 0xDD else "IY"
    n = mem.next_byte()
    ofs = uint8_to_int8(n)
    sign = "-" if ofs < 0 else "+"
    p = (op2 >> 3) & 7
    return f"{ARITHMETIC[p]} ({ixy}{sign}${abs(ofs):02X})"



MNEMONIC_DD_FD = {
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
    0x86: arithmetic_indexed,
    0xE1: lambda op, *_: "POP IX" if op == 0xDD else "POP IY",
    0xE5: lambda op, *_: "PUSH IX" if op == 0xDD else "PUSH IY",
    0xE3: lambda op, *_: "EX (SP),IX" if op == 0xDD else "EX (SP),IY",
    0xE9: lambda op, *_: "JP (IX)" if op == 0xDD else "JP (IY)",
    0xF9: lambda op, *_: "LD SP,IX" if op == 0xDD else "LD SP,IY",
    0xCB: bit_shift,
}


def init_instruction_dict():
    for n in range(1, 4):
        MNEMONIC_DD_FD[0x09 + n * 0x10] = MNEMONIC_DD_FD[0x09]  # LD ixy,REG16

    for n in range(1, len(REG8)):
        MNEMONIC_DD_FD[0x46 + n * 8] = MNEMONIC_DD_FD[0x46]  # LD r,(ixy+n)
        MNEMONIC_DD_FD[0x70 + n] = MNEMONIC_DD_FD[0x70]  # LD r,(ixy+n)

    for n in range(1, len(ARITHMETIC)):
        MNEMONIC_DD_FD[0x86 + n * 8] = MNEMONIC_DD_FD[0x86]  # arithmetic


init_instruction_dict()
