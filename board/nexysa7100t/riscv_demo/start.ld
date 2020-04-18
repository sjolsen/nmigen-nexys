MEMORY {
    /* TODO: Generate the memory map from a single source of truth */
    /* TODO: Revert to 4 kiB when https://github.com/nmigen/nmigen/issues/359
       is fixed */
    brom (RXAL) : ORIGIN = 0x00000000, LENGTH = 0x800
    bram (WXAL) : ORIGIN = 0x00001000, LENGTH = 0x800
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
        __data_start = .;
        *(.data*)
        . = ALIGN(4);
        __data_end = .;
    } >bram AT>brom
    __data_load = LOADADDR(.data);

    .bss : {
        __bss_start = .;
        . += 0x400;
        __stack_top = .;
        *(.bss*)
        __bss_end = .;
    } >bram

    .periph ORIGIN(periph) : {
        __periph_start = .;
    } >periph
}
