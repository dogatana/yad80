REG8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
REG16_SP = ["BC", "DE", "HL", "SP"]
REG16_AF = ["BC", "DE", "HL", "AF"]

ARITHMETIC = ["ADD A,", "ADC A,", "SUB ", "SBC A,", "AND ", "XOR ", "OR ", "CP "]
ROTATE_SHIFT = ["RLCA", "RRCA", "RLA", "RRA", "DAA", "CPL", "SCF", "CCF"]

ROTATE_SHIFT_R = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", None, "SRL"]
BIT_OP = [None, "BIT", "RES", "SET"]

CC = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]


def uint8_to_int8(value):
    if value <= 127:
        return value
    else:
        return value - 256
