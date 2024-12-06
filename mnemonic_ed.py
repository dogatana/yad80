REG8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
REG16_SP = ["BC", "DE", "HL", "SP"]


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
    0x4a: adc_hl,
    0x43: ld_mem_rr,
    0x53: ld_mem_rr,
    0x63: ld_mem_rr,
    0x73: ld_mem_rr,
    0x4b: ld_rr_mem,
    0x6b: ld_rr_mem,
    0x5b: ld_rr_mem,
    0x7b: ld_rr_mem,
    0x47: lambda *_: "LD I,A",
    0x57: lambda *_: "LD A,I",
    0x4f: lambda *_: "LD R,A",
    0x5f: lambda *_: "LD A,R",
    0xa0: lambda *_: "LDI",
    0xa8: lambda *_: "LDD",
    0xb0: lambda *_: "LDIR",
    0xb8: lambda *_: "LDDR",
    0xa1: lambda *_: "CPI",
    0xa9: lambda *_: "CPD",
    0xb1: lambda *_: "CPIR",
    0xb9: lambda *_: "CPDR",
    0xa2: lambda *_: "INI",
    0xaa: lambda *_: "IND",
    0xb2: lambda *_: "INIR",
    0xba: lambda *_: "INDR",
    0xa3: lambda *_: "OUTI",
    0xab: lambda *_: "OUTD",
    0xb3: lambda *_: "OTIR",
    0xbb: lambda *_: "OTDR",
    0x44: lambda *_: "NEG",
    0x45: lambda *_: "RETN",
    0x4d: lambda *_: "RETI",
    0x46: lambda *_: "IM 0",
    0x56: lambda *_: "IM 1",
    0x5e: lambda *_: "IM 2",
    0x67: lambda *_: "RRD",
    0x6f: lambda *_: "RLD",
}


def init_instruction_dict():
    for n in range(1, 8):
        MNEMONIC_ED[0x40 + n * 8] = MNEMONIC_ED[0x40]  # IN r,(C)
        MNEMONIC_ED[0x41 + n * 8] = MNEMONIC_ED[0x41]  # OUT (C),r

    for n in range(1, len(REG16_SP)):
        MNEMONIC_ED[0x42 + n * 0x10] = MNEMONIC_ED[0x42]  # SBC HL,rr
        MNEMONIC_ED[0x4a + n * 0x10] = MNEMONIC_ED[0x4a]  # ADC HL,rr


init_instruction_dict()
