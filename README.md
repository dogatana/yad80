# yad80 - Yet Another Disassembler for Z80

## Introduction

yad80 is a Z80 disassembler that outputs an assembler source.

## Install yad80

```
pip install yad80
```

## Description

### Disassemblable Z80 Instructions

- Instructions defined in Zilog's [Z80 CPU User Manual](https://www.zilog.com/docs/z80/um0080.pdf)<br>[https://github.com/dogatana/yad80/blob/main/tests/zilog.asm](https://github.com/dogatana/yad80/blob/main/tests/zilog.asm)
- Undocumented Instructions for IXH, IXL, IYH, and IYL in Zilog's Z80 CPU User Manual<br>
unpublished instructions<>
<br>[https://github.com/dogatana/yad80/blob/main/tests/undocumented_ixy.asm](https://github.com/dogatana/yad80/blob/main/tests/undocumented_ixy.asm)

### Input files

- Machine language file with .mzt extension (hereafter __mzt file__)
    - Attribute (file mode) must be $01.
    - mzt files containing multiple data cannot be handled.
- Machine language file without address information (hereafter __bin files__).
    - The file extension is arbitrary.
    - If the first address of the file is not $0000, specify it with the `--offset` option.

### Output of Disassembly Results

- Disassembly results are output to standard output. Redirect to a file if necessary.
- I have confirmed that the output can be assembled with the z88dk assembler. Other assemblers have not been checked.

### Operation Modes

yad80 has the following two modes of operation, which are selected by runtime options.

- simple Disassemble (hereafter __simple__)
    - This is the mode of operation without the `--eager` option.
    - Disassembles from the specified address until it finds a given number of lines, the end of a file, or an invalid instruction.
    - Start address
        - If `--addr` option is specified, the address
        - If not specified by the `--addr` option, the bin file is the top address of the file, and the mzt file is the execution start address in the header.
- eager Disassembly (eager)
    - The mode of operation with `--eager` option.
    - Start address
        - The start address is the same as for simple.
        - If multiple start addresses are specified in the `--addr` option, all of them are treated as start addresses.
        - Disassembles from the specified address to an executable range such as an unconditional branch.
    - Address range specification
        - An address range can be specified.
        - Disassembles the entire specified address range as a sequence of valid instructions. Disassembly continues even if there is a branch or stop instruction on the way.
    - Disassembles the reachable range
        - Disassembles the branch address detected during disassembly as the start address. As a result, the entire reachable range from the specified address and address range is disassembled.
    - Data
        - The address range to be handled as data (byte string) can be specified and output in `DB`.
        - Of the address range of the input file, data areas not reached by disassembly are output in `DB`.
    - String
        The range to be treated as a character string can be specified and is output as a character string, such as `DB "ASCII".`
        Generates a label for the first address.
    - Label Generation
        - Generates labels for branch destination addresses.
        - Generates labels for the string and the first address in the specified address range.
        - Generates labels for memory references such as `($ABCD)`.
        - Does not generate labels for direct values such as `LD HL, $ABCD`, etc.
        - Adds `EQU` definitions for addresses that are not in the address range of the input file, such as calls to routines in ROM, access to VRAM, memory-mapped IO, etc.
    - Cross Reference
        - Cross reference information for each label is output as a comment following the disassembly output.
    - Data Definition Area Summary
        - Following the cross reference output, the ASCII output at the beginning of the DB definition contents is output as a commented summary.

### Generated Labels

- `JR`, `JP`, and `CD` correspond to relative jumps, absolute jumps, and calls, respectively. If there are multiple branches for the same address, labels are generated that include all of them.
- `ST` corresponds to a string.
- `DT` corresponds to a memory reference.
- Labels beginning with `EX` are addresses outside the address range of the input file.
- Output example
```
EX_DT_E000 EQU $e000
                ORG $0000
                JP JP_004A
CD_0003: JP JP_07E6
CDJP_0006: JP JP_090E
```
- In the case of a self-rewriting code, the label is defined as an `EQU` definition, but it is not (and cannot be) output as the first address of the instruction.<br>However, the `; within CODE comment` is added to the EQU definition.
```
DT_460C EQU $460c ; within CODE

                LD (DT_460C),A
                LD A,(IX+$02)
                BIT 0,C
                JR Z,JR_460B
                DEC A

JR_460B: ADD A,$00
                CALL CD_45F2
```

### Instruction to be regarded as a branch 

- `JR`
- `JR`
- `DJNZ`
- `CALL`

### Instruction to stop disassembling with eager

- Unconditional `JP`
- Unconditional `JR`
- `RET`, `RETI`, `RETN`
- `HALT`

## Usage

### Options

```
> yad80 -h
usage: yad80 [-h] [--version] [--option OPTION] [--code [RANGE ...]] [--string [RANGE ...]] [--addr [ADDR ...]]
             [--eager] [--debug] [--max-lines N] [--offset OFFSET]
             FILE

positional arguments:
  FILE                  file to disasm

options:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --option OPTION       option file
  --code [RANGE ...], -c [RANGE ...]
                        address range(a1-a2) as code. a2 is an inclusive address
  --string [RANGE ...], -s [RANGE ...]
                        address range(a1-a2) as string. a2 is an inclusive address
  --addr [ADDR ...], -a [ADDR ...]
                        address to disasm
  --eager, -e           disasm eagerly(default false)
  --debug               debug flag(dev use)
  --max-lines N, -m N   max lines to output(default 32)
  --offset OFFSET, -o OFFSET
                        address offset for binary file
```

### Option explanations

- `--eager`
    - Specify eager.
- `--option OPTION` (simple, eager)
    - Specifies a file containing options.
    - Individual options take precedence over this specification.
    - In the file, the `;` and  `#` character are start of line comment.

```
# OPTION example
-e # eager
-c 0-79 # JP xxxx 

# string defs
ST_0131: DB “FOUND ”,$0D                      
ST_0138: DB “LOADING ”,$0D                    
ST_0141: DB “** MZ”,$90, “MONITOR VER4.4 **”,$0D

; $0131-$0158, [$ 28] FOUND .LOADING . ** MZ.MONITOR VER4.4 **.
-s 131-137 ; FOUND
-s 138-140 ; LOADING
-s 141-158 ; ** MZ.MONITOR....
```
- `--code RANGE` (eager)
    - Disassemble the entire specified range, regardless of whether it contains instructions to stop disassembly.
- `--string RANGE` (eager)
    - Define the specified range as a string in `DB`.
- `--addr ADDR` (simple, eager)
    - Specify an address to start disassembling.
- `--max-lines N` (simple)
    - Specify the number of lines to disassemble. If not specified, up to 32 lines are disassembled.
- `--offset OFFSET` (simple, eager)
    - In the case of a bin file, specify the address in hexadecimal where the machine language is actually located.

__ADDR__, __OFFSET__

- Specifies the address as a hexadecimal string. The $, 0x, H, etc. are not necessary.

__RANGE (address range)__

- The range is specified in the format `[start address]-[end address]` with no spaces in between.
- The end address is included in the address range.
- The start and end addresses are specified as hexadecimal character strings.
- Example: `0-79` This is $0000-$0079.

__FILE__

- Multiple-valued options and `FILE` must be preceded by `--` (end of option).

End of document