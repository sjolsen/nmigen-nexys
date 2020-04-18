# /opt/riscv32/bin/riscv32-unknown-elf-gcc board/nexysa7100t/riscv_demo/start.S -ffreestanding -nostdlib -Wl,-Tboard/nexysa7100t/riscv_demo/start.ld -o board/nexysa7100t/riscv_demo/start.elf
# /opt/riscv32/bin/riscv32-unknown-elf-objcopy -I elf32-littleriscv -O binary board/nexysa7100t/riscv_demo/start.elf board/nexysa7100t/riscv_demo/start.bin

.global __data_start
.global __data_end
.global __data_load

.global __bss_start
.global __bss_end

.global __stack_top

.global main

.section .text
.global _start
_start:
0:  la t0, __data_load
    la t1, __data_start
    la t2, __data_end
1:  lw t3, 0(t0)
    sw t3, 0(t1)
    addi t0, t0, 4
    addi t1, t1, 4
    blt t1, t2, 1b
2:  la t1, __bss_start
    la t2, __bss_end
3:  sw zero, 0(t1)
    addi t1, t1, 4
    blt t1, t2, 3b
4:  la sp, __stack_top
    jal main
5:  nop  # Minerva does not implement wfi
    j 5b
