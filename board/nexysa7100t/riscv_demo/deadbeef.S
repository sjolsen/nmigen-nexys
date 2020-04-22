# /opt/riscv32/bin/riscv32-unknown-elf-gcc board/nexysa7100t/riscv_demo/start.S -ffreestanding -nostdlib -Wl,-Tboard/nexysa7100t/riscv_demo/start.ld -o board/nexysa7100t/riscv_demo/start.elf
# /opt/riscv32/bin/riscv32-unknown-elf-objcopy -I elf32-littleriscv -O binary board/nexysa7100t/riscv_demo/start.elf board/nexysa7100t/riscv_demo/start.bin

.global __periph_start

.section .text.start
.global _start
_start:
1:  la t0, __periph_start
    li t1, 0xdeadbeef
    sw t1, 0(t0)
2:  nop  # Minerva does not implement wfi
    j 2b

.section .rodata

.section .data

.section .bss
