# yad80 - Yet Another Disassembler for Z80

## Introduction

yad80 is a Z80 disassembler that outputs an assembler source that can be assembled by z80asm.

## Install yad80

```
pip install yad80
```

## Specification

### Z80 Instructions

- Instructions defined in Zilog's [Z80 CPU User Manual](https://www.zilog.com/docs/z80/um0080.pdf).  ([zilog.asm](https://github.com/dogatana/yad80/blob/main/tests/zilog.asm))
- Undocumented Instructions for IXH, IXL, IYH, and IYL. ([undocumented_ixy.asm](https://github.com/dogatana/yad80/blob/main/tests/undocumented_ixy.asm))

### Input files

- Machine language file with .mzt extension (hereafter __mzt file__).
    - Attribute (file mode) must be $01.
    - mzt files containing multiple data blocks cannot be handled.
- Machine language file without address information (hereafter __bin files__).
    - The file extension is arbitrary.
    - If the first address of the file is not $0000, specify it with the `--offset` option.

### Output of Disassembly Results

- Result is output to standard output. Redirect it to a file if necessary.
- I have confirmed that the output can be assembled with z80asm, z88dk assembler.

### Operation Modes

yad80 has the following two modes of operation, which are selected by runtime option(`--eager`).

- Simple disassemble (hereafter __Simple__)
    - This is the mode of operation without the `--eager` option.
    - Disassembles from the specified start address until it finds a given number of lines, the end of a file, or an invalid instruction.
    - Start address
        - If `--addr` option is specified, the address
        - If not specified by the `--addr` option, the start address of the file for the bin file, or the start address in the mzt file header is used.
- Eager disassembe (Eager)
    - The mode of operation with `--eager` option.
    - Start address
        - The start address is the same as for simple.
        - If multiple start addresses are specified with `--addr` option, all of them are treated as start addresses one by one.
        - Disassembles from the specified address to an executable range such as an unconditional branch.
    - Address range specification
        - An address range can be specified with `--code` option.
        - Disassembles the entire specified address range as a sequence of valid instructions. Disassembly continues even if there is a branch or stop instruction on the way.
    - Disassembles the reachable range
        - Disassembles the branch address detected during disassembly as the start address. As a result, the entire reachable instructions are disassembled.
    - Data
        - The address range to be handled as data (byte array) can be specified and output in `DB`.
        - Of the address range of the input file, data areas not reached by disassembly are output in `DB`.
    - String
        - The range to be treated as a character string can be specified and is output as a character string, such as `DB "ASCII".`
        - Generates a label for the first address.
    - Label Generation
        - Generates labels for branch destination addresses.
        - Generates labels for the string and the first address.
        - Generates labels for memory references such as `($ABCD)`.
        - Does __not__ generate labels for immediate values such as `LD HL,$ABCD`, etc.
        - Adds `EQU` definitions for addresses that are not in the address range of the input file, such as calls to ROM routines, access to VRAM, memory-mapped I/O, etc.
    - Cross Reference
        - Cross reference information for each label is output as a comment following the disassembly output.
    - Data Definition Area Summary
        - Following the cross reference output, data block information is output as a comment.

```
; XREF information
; CD_0003         $0092
; CDJP_0006       $089e $091d $0c51
; CD_0009         $0089 $0452

; DATA summary
; $010e-$010e, [$  1] .
; $0179-$0191, [$ 19] !........... ..(...(..#..
; $019a-$019e, [$  5] >....
; $01b4-$01c6, [$ 13] .CHECKSUM ERROR.OK.
```


### Generated Labels

- `JR`, `JP`, and `CD` correspond to relative jumps, absolute jumps, and calls, respectively. If there are multiple branches for the same address, labels are generated that include all of them.
- `ST` corresponds to a string.
- `DT` corresponds to a memory reference.
- Labels beginning with `EX` are addresses outside the address range of the input file.
- Output example
```
EX_DT_E000      EQU $e000

                ORG $0000

                JP JP_004A
CD_0003:        JP JP_07E6
CDJP_0006:      JP JP_090E
```
- In the case of a self-rewriting code, the label is defined as an `EQU` definition, but it is not (and cannot be) output as the first address of the instruction.<br>However, the `; within CODE comment` is added to the EQU definition.
```
DT_460C         EQU $460c ; within CODE

                LD (DT_460C),A
                LD A,(IX+$02)
                BIT 0,C
                JR Z,JR_460B
                DEC A

JR_460B:        ADD A,$00
                CALL CD_45F2
```

### Instruction to be regarded as a branch 

- `JR`
- `JR`
- `DJNZ`
- `CALL`

### Instruction to stop disassembling

- Unconditional `JP`
- Unconditional `JR`
- `RET`, `RETI`, `RETN`
- `HALT`

## Usage

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

### Options

- `--eager`
    - Specify eager.
- `--option OPTION` (simple, eager)
    - Specifies a file containing options.
    - Individual options take precedence over this specification.
    - In the file, the `;` and  `#` character are treated as the start of line comment.

```
# OPTION example
-e # eager
-c 0-79 # JP xxxx 

# string defs
-s 131-137 ; FOUND
-s 138-140 ; LOADING
-s 141-158 ; ** MZ.MONITOR....

; $0131-$0158, [$ 28] FOUND .LOADING . ** MZ.MONITOR VER4.4 **.
; 
; ST_0131:        DB    "FOUND ",$0D  
; ST_0138:        DB    "LOADING ",$0D
; ST_0141:        DB    "** MZ",$90,"MONITOR VER4.4 **",$0D
```
- `--code RANGE` (eager)
    - Disassemble the entire specified range, regardless of whether it contains instructions to stop disassembly.
- `--string RANGE` (eager)
    - Define the specified range as a string in `DB`.
- `--addr ADDR` (simple, eager)
    - Specify a starting address to disassembe.
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
- ex) `0-79` This is $0000-$0079.

__FILE__

- Multiple-valued options and `FILE` must be preceded by `--` (end of option).

## ChangeLog

- v0.1.5 Bug fix: Dose not create DB when minimum address < start address
- v0.1.4 Bug fix: `--addr` option
- v0.1.3 Insert some spaces after EQU
- v0.1.2 Bug fix: `--offset` option
- v0.1.0 public release

End of document