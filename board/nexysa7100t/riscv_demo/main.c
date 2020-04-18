#include <stdint.h>

extern unsigned char __periph_start;

#define REG32(_addr) (*(volatile uint32_t*)(_addr))
#define SSEG_DATA REG32(&__periph_start)

__attribute__((noreturn))
int main() {
    uint32_t i = 0;
    while (1) {
        SSEG_DATA = i;
        ++i;
    }
}
