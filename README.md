# ElfDisassembler

## About

The program is a disassembler of *.elf files (32 bits). That is, a translator with which you can convert machine code into the text of a program in assembly language

ISA that the program works with: RISC-V RV32I, RV32M, RVC

Encoding: little endian

The program processes sections .text and .symtab

## Run

To run the program, use `Python 3.10`:

> python Elf_Disassembler.py < name_input_file > < name_output_file >

## Example of the result

```
.text
00010074 register_fini ADDI a5, zero, 0
00010078            BEQ a5, zero, 16 0x00010088 LOC_10088
0001007c            LUI a0, 65536
00010080            ADDI a0, a0, 1164
00010084            JAL zero, 1012 0x00010478 atexit
00010088 LOC_10088: JALR zero, 0(ra)
0001008c     _start AUIPC gp, 8192
00010090            ADDI gp, gp, -684
00010094            ADDI a0, gp, -972
00010098            ADDI a2, gp, -944
0001009c            SUB a2, a2, a0
000100a0            ADDI a1, zero, 0
000100a4            JAL ra, 472 0x0001027c memset
000100a8            AUIPC a0, 0
000100ac            ADDI a0, a0, 976
...

.symtab
Symbol Value              Size Type     Bind     Vis       Index Name
[   0] 0x0                   0 NOTYPE   LOCAL    DEFAULT   UNDEF 
[   1] 0x10074               0 SECTION  LOCAL    DEFAULT       1 
[   2] 0x115cc               0 SECTION  LOCAL    DEFAULT       2 
[   3] 0x115d0               0 SECTION  LOCAL    DEFAULT       3 
[   4] 0x115d8               0 SECTION  LOCAL    DEFAULT       4 
[   5] 0x115e0               0 SECTION  LOCAL    DEFAULT       5 
[   6] 0x11a08               0 SECTION  LOCAL    DEFAULT       6 
[   7] 0x11a14               0 SECTION  LOCAL    DEFAULT       7 
[   8] 0x0                   0 SECTION  LOCAL    DEFAULT       8 
[   9] 0x0                   0 SECTION  LOCAL    DEFAULT       9 
[  10] 0x0                   0 FILE     LOCAL    DEFAULT     ABS __call_atexit.c
[  11] 0x10074              24 FUNC     LOCAL    DEFAULT       1 register_fini
[  12] 0x0                   0 FILE     LOCAL    DEFAULT     ABS crtstuff.c
[  13] 0x115cc               0 OBJECT   LOCAL    DEFAULT       2 
[  14] 0x100d8               0 FUNC     LOCAL    DEFAULT       1 __do_global_dtors_aux
[  15] 0x11a14               1 OBJECT   LOCAL    DEFAULT       7 completed.1
[  16] 0x115d8               0 OBJECT   LOCAL    DEFAULT       4 __do_global_dtors_aux_fini_array_entry
[  17] 0x10124               0 FUNC     LOCAL    DEFAULT       1 frame_dummy
[  18] 0x11a18              24 OBJECT   LOCAL    DEFAULT       7 object.0
[  19] 0x115d4               0 OBJECT   LOCAL    DEFAULT       3 __frame_dummy_init_array_entry
...
```


