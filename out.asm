
# Tungsten Compiler
# Constants
.set void 0
.set byte 1
.set int 2
.set ptr 2


# Tungsten Compiler
# Generated code
.section text

.label __TUNGSTEN_START_add_bytes
ldrx BUFFER_add_bytes_a
ldry BUFFER_add_bytes_b
addxy
strx __TUNGSTEN_FUNCION_RETVAL
.label __TUNGSTEN_END_add_bytes
.label _main
.label __TUNGSTEN_START_main
ldx 0x50
out
.label __TUNGSTEN_END_main

# Tungsten Compiler
# Generated data
.section data
.label _swap
.alloc 2
.label __TUNGSTEN_FUNCTION_JBA
.alloc 2
.label __TUNGSTEN_FUNCION_RETVAL
.alloc 2

.label BUFFER_add_bytes_a
.alloc 1
.label BUFFER_add_bytes_b
.alloc 1
.label BUFFER_main_testaw
.alloc 2