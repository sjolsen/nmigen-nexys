MEMORY {
    brom (RXAL) : ORIGIN = 0x00000000, LENGTH = 32 * 1024
    bram (WXAL) : ORIGIN = 0x00001000, LENGTH = 32 * 1024
    periph (W!XAL) : ORIGIN = 0x00002000, LENGTH = 0x100
}

ENTRY(_start)

SECTIONS {
    .reset : AT(0x00000000) {
        LONG(_start)
    } >brom
    ASSERT((SIZEOF(.reset) == 4), "Reset vector not of length 4")

    .text : {
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
