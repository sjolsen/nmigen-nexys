"""Tools for working with binary-coded decimal (BCD)."""

from nmigen import *
from nmigen.build import *


class BinToBCD(Elaboratable):
    """Convert binary to BCD.

    Rather than implementing a large swath of combinatorial logic, this
    implementation runs a multi-cycle conversion algorithm. The conversion time
    is proportional to the number of output digits. The output is little-endian.
    """

    def __init__(self, input: Signal, output: [Signal]):
        super().__init__()
        self.input = input
        self.start = Signal(reset=0)
        self.output = output
        self.done = Signal(reset=0)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        input = Signal(self.input.width)
        output = Cat(*self.output)
        cursor = Signal(range(len(self.output)), reset=len(self.output) - 1)
        div = Signal(input.width)
        mod = Signal(4)
        m.d.comb += div.eq(input // 10)
        m.d.comb += mod.eq(input % 10)
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += input.eq(self.input)
                    m.d.sync += cursor.eq(cursor.reset)
                    m.next = 'CONVERT'
            with m.State('CONVERT'):
                m.d.sync += output.eq(Cat(output[4:], mod))
                m.d.sync += input.eq(div)
                m.d.sync += cursor.eq(cursor - 1)
                with m.If(cursor == 0):
                    m.d.sync += self.done.eq(1)
                    m.next = 'DONE'
            with m.State('DONE'):
                m.d.sync += self.done.eq(0)
                m.next = 'IDLE'
        return m
