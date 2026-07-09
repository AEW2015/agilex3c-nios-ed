ENTRY(_start)

MEMORY
{
    ram (rwx) : ORIGIN = 0x08000000, LENGTH = 64K
}

SECTIONS
{
    .text : {
        *(.text.entry)
        *(.text*)
        *(.rodata*)
    } > ram

    .data : {
        *(.data*)
    } > ram

    .bss : {
        *(.bss*)
        *(COMMON)
    } > ram
}
