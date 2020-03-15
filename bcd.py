from nmigen import *
from nmigen.build import *


class DigitLUT(Elaboratable):

    # 7-bit encoding of segments A-G, indexed by value
    TABLE = [
        0b0111111,
        0b0000110,
        0b1011011,
        0b1001111,
        0b1100110,
        0b1101101,
        0b1111101,
        0b0000111,
        0b1111111,
        0b1101111,
    ]

    def __init__(self, input: Signal):
        super().__init__()
        self.input = input
        self.output = Signal(8)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        with m.Switch(self.input):
            for i, val in enumerate(self.TABLE):
                with m.Case(i):
                    m.d.comb += self.output.eq(val)
            with m.Case():
                m.d.comb += self.output.eq(0)
        return m


class BCDRenderer(Elaboratable):

    def __init__(self, input: [Signal]):
        super().__init__()
        assert len(input) != 0
        self.input = input
        self.start = Signal(reset=0)
        self.output = [Signal(8) for _ in input]
        self.done = Signal(reset=0)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        input = Signal(4 * len(self.input))
        current_input = input[-4:]
        output = Cat(*self.output)
        current_output = Signal(8)
        cursor = Signal(range(len(self.input)), reset=len(self.input) - 1)
        seen_nonzero = Signal()
        m.submodules.lut = lut = DigitLUT(current_input)
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += input.eq(Cat(*self.input))
                    m.d.sync += cursor.eq(cursor.reset)
                    m.d.sync += seen_nonzero.eq(0)
                    m.next = 'CONVERT'
            with m.State('CONVERT'):
                is_zero = (current_input == 0).bool()
                leading_zero = ~seen_nonzero.bool() & is_zero
                blank_zero = leading_zero & (cursor != 0).bool()
                with m.If(blank_zero):
                    m.d.comb += current_output.eq(0)
                with m.Else():
                    m.d.comb += current_output.eq(lut.output)
                m.d.sync += cursor.eq(cursor - 1)
                m.d.sync += seen_nonzero.eq(seen_nonzero | ~is_zero)
                with m.If(cursor == 0):
                    m.next = 'DONE'
                    m.d.sync += self.done.eq(1)
                m.d.sync += input.eq(input << 4)
                m.d.sync += output.eq(Cat(current_output, output[:-8]))
            with m.State('DONE'):
                m.d.sync += self.done.eq(0)
                m.next = 'IDLE'
        return m


class BinToBCD(Elaboratable):

    def __init__(self, input: Signal, output: [Signal]):
        super().__init__()
        self.input = input
        self.start = Signal(reset=0)
        self.output = output
        self.done = Signal(reset=0)

    def elaborate(self, platform: Platform) -> Module:
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
