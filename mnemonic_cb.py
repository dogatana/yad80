from exceptions import InstructionError

REG8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
ROTATE_SHIFT_R = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", None, "SRL"]
BIT_OP = [None, "BIT", "RES", "SET"]


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


MNEMONIC_CB = {
    0x00: rotate_shift_r,
    0x40: bit_operation,
}


def init_instruction_hash():
    for n in range(1, 0x40):
        MNEMONIC_CB[n] = MNEMONIC_CB[0]  # rotate r, shift r
    for n in range(0x41, 0x100):
        MNEMONIC_CB[n] = MNEMONIC_CB[0x40]  # bit operation


init_instruction_hash()
