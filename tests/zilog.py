"""create code for ixh, ixl, iyh asd iyl"""

REG8 = "A B C D E H L".split()
REG16_SP = "BC DE HL SP".split()
CC = "NZ Z NC C PO PE P M".split()

for r1 in REG8:
    for r2 in REG8:
        print(f"LD {r1},{r2}")

for r1 in REG8:
    print(f"LD {r1},$12")
for r1 in REG8:
    print(f"LD {r1},(HL)")
for r1 in REG8:
    print(f"LD {r1},(IX + 1)")
for r1 in REG8:
    print(f"LD {r1},(IY - 1)")
for r1 in REG8:
    print(f"LD (HL),{r1}")
for r1 in REG8:
    print(f"LD (IX + 1),{r1}")
for r1 in REG8:
    print(f"LD (IY - 1),{r1}")

print("LD (HL),$12")
print("LD (IX + 1),$12")
print("LD (IY - 1),$12")

for r in "BC DE $5678".split():
    print(f"LD A,({r})")
for r in "BC DE $5678".split():
    print(f"LD ({r}),A")

print("LD A,I")
print("LD A,R")
print("LD I,A")
print("LD R,A")

for r in "BC DE HL SP".split():
    print(f"LD {r},$5678")

print("LD IX,$5678")
print("LD IY,$5678")

print("LD HL,($5678)")
# print("db $ed,$6b,$78,$56")  # LD HL,($5678) alt

for r in "BC DE HL SP".split():
    print(f"LD {r},($5678)")

print("LD IX,($5678)")
print("LD IY,($5678)")


print("LD ($5678),HL")
# print("db $ed,$63,$78,$56")  # LD ($5678),HL alt

for r in "BC DE HL SP".split():
    print(f"LD ($5678),{r}")

print("LD ($5678),IX")
print("LD ($5678),IY")

print("LD SP,HL")
print("LD SP,IX")
print("LD SP,IY")

for r in "BC DE HL AF".split():
    print(f"PUSH {r}")

print("PUSH IX")
print("PUSH IY")

for r in "BC DE HL AF".split():
    print(f"POP {r}")

print("POP IX")
print("POP IY")


print("EX DE,HL")
print("EX AF,AF'")
print("EXX")
print("EX (SP),HL")
print("EX (SP),IX")
print("EX (SP),IY")

print("LDI")
print("LDIR")
print("LDD")
print("LDDR")
print("CPI")
print("CPIR")
print("CPD")
print("CPDR")


for op in ["ADD A,", "ADC A,", "SBC A,"]:
    for r in REG8:
        print(f"{op}{r}")
    print(f"{op}$12")
    print(f"{op}(HL)")
    print(f"{op}(IX+1)")
    print(f"{op}(IX-1)")

for op in "SUB AND OR XOR CP".split():
    for r in REG8:
        print(f"{op} {r}")
    print(f"{op} $12")
    print(f"{op} (HL)")
    print(f"{op} (IX+1)")
    print(f"{op} (IX-1)")

for op in "INC DEC".split():
    for r in REG8:
        print(f"{op} {r}")
    print(f"{op} (HL)")
    print(f"{op} (IX+1)")
    print(f"{op} (IY-1)")

print("DAA")
print("CPL")
print("NEG")
print("CCF")
print("SCF")
print("NOP")
print("HALT")
print("DI")
print("EI")
print("IM 0")
print("IM 1")
print("IM 2")

for op in ["ADD", "ADC", "SBC"]:
    for r in REG16_SP:
        print(f"{op} HL,{r}")

for r in "BC DE IX SP".split():
    print(f"ADD IX,{r}")
for r in "BC DE IY SP".split():
    print(f"ADD IY,{r}")

for r in REG16_SP:
    print(f"INC {r}")
print("INC IX")
print("INC IY")

for r in REG16_SP:
    print(f"DEC {r}")
print("DEC IX")
print("DEC IY")

print("RLCA")
print("RLA")
print("RRCA")
print("RRA")

for op in "RLC RL RRC RR SLA SRA SRL".split():
    for r in REG8:
        print(f"{op} {r}")
    print(f"{op} (HL)")
    print(f"{op} (IX+1)")
    print(f"{op} (IY-1)")

print("RLD")
print("RRD")

for op in "BIT SET RES".split():
    for r in REG8:
        for n in range(8):
            print(f"{op} {n},{r}")
        for n in range(8):
            print(f"{op} {n},(HL)")
    for n in range(8):
        print(f"{op} {n},(IX+1)")
    for n in range(8):
        print(f"{op} {n},(IY-1)")

print("JP $5678")

for cc in CC:
    print(f"JP {cc},$5678")

print("LABEL:")
print("JR LABEL")

for cc in CC[:4]:
    print(f"JR {cc},LABEL")

print("JP (HL)")
print("JP (IX)")
print("JP (IY)")

print("DJNZ LABEL")

print("CALL $5678")
for cc in CC:
    print(f"CALL {cc},$5678")

print("RET")
for cc in CC:
    print(f"RET {cc}")
print("RETI")
print("RETN")

for n in range(0, 0x40, 8):
    print(f"RST ${n:02X}")

print("IN A,($12)")
for r in REG8:
    print(f"IN {r},(C)")
print("INI")
print("INIR")
print("IND")
print("INDR")

print("OUT ($12),A")
for r in REG8:
    print(f"OUT (C),{r}")
print("OUTI")
print("OTIR")
print("OUTD")
print("OTDR")
