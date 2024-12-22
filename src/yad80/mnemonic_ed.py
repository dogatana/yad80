from .mnemonic_defs import REG8, REG16_SP


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


MNEMONIC_ED = {
    0x40: in_r,
    0x41: out_r,
    0x42: sbc_hl,
    0x4A: adc_hl,
    0x43: ld_mem_rr,
    0x53: ld_mem_rr,
    0x63: ld_mem_rr,
    0x73: ld_mem_rr,
    0x4B: ld_rr_mem,
    0x6B: ld_rr_mem,
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


def init_instruction_dict():
    for n in range(1, 8):
        MNEMONIC_ED[0x40 + n * 8] = MNEMONIC_ED[0x40]  # IN r,(C)
        MNEMONIC_ED[0x41 + n * 8] = MNEMONIC_ED[0x41]  # OUT (C),r

    for n in range(1, len(REG16_SP)):
        MNEMONIC_ED[0x42 + n * 0x10] = MNEMONIC_ED[0x42]  # SBC HL,rr
        MNEMONIC_ED[0x4A + n * 0x10] = MNEMONIC_ED[0x4A]  # ADC HL,rr


init_instruction_dict()
