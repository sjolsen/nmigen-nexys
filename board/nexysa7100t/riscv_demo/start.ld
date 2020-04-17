MEMORY {
    /* TODO: Generate the memory map from a single source of truth */
    brom (RXAL) : ORIGIN = 0x00000000, LENGTH = 32 * 1024
    bram (WXAL) : ORIGIN = 0x00001000, LENGTH = 32 * 1024
    periph (W!XAL) : ORIGIN = 0x00002000, LENGTH = 0x100
}

ENTRY(_start)

SECTIONS {
    .text : AT(0x00000000) {
        _start = .;
        *(.text*)
    } >brom

    .rodata : {
        *(.rodata*)
    } >brom

    .data : {
        *(.data*)
    } >bram AT>brom

    .bss : {
        *(.bss*)
    } >bram

    .periph ORIGIN(periph) : {
        __periph_start = .;
    } >periph
}
