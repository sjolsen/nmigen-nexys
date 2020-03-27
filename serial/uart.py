import fractions

from nmigen import *
from nmigen.build import *

from nmigen_nexys.core import edge
from nmigen_nexys.core import shift_register
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import util


class Transmit(Elaboratable):

    def __init__(self, baud_rate: int):
        super().__init__()
        self.baud_rate = baud_rate
        self.data = Signal(8)
        self.start = Signal()
        self.busy = Signal(reset=0)
        self.done = Signal(reset=0)
        self.output = Signal(reset=1)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        m.submodules.timer = timer = timer_module.UpTimer(
            period=fractions.Fraction(util.GetClockFreq(platform),
                                      self.baud_rate))
        m.submodules.symbols = symbols = shift_register.Down(10, reset=0x3FF)
        m.d.comb += symbols.word_in.eq(Cat(C(0, 1), self.data, C(1, 1)))
        m.d.comb += symbols.bit_in.eq(1)
        m.d.comb += symbols.shift.eq(self.busy & timer.triggered)
        m.d.comb += self.output.eq(symbols.bit_out)
        remaining = Signal(range(10 + 1))

        m.d.sync += timer.reload.eq(0)  # default
        m.d.comb += symbols.latch.eq(0)  # default
        m.d.sync += self.done.eq(0)  # default
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += self.busy.eq(1)
                    m.d.sync += timer.reload.eq(1)
                    m.d.comb += symbols.latch.eq(1)
                    m.d.sync += remaining.eq(10)
                    m.next = 'RUN'
            with m.State('RUN'):
                with m.If(timer.triggered):
                    m.d.sync += remaining.eq(remaining - 1)
                    with m.If(remaining == 1):
                        m.d.sync += self.busy.eq(0)
                        m.d.sync += self.done.eq(1)
                        m.next = 'IDLE'
        return m


class Receive(Elaboratable):

    def __init__(self, baud_rate: int):
        super().__init__()
        self.baud_rate = baud_rate
        self.input = Signal()
        self.data = Signal(8, reset=0)
        self.start = Signal(reset=0)
        self.busy = Signal(reset=0)
        self.done = Signal(reset=0)
        self.error = Signal(reset=0)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        m.submodules.timer = timer = timer_module.UpTimer(
            period=fractions.Fraction(util.GetClockFreq(platform),
                                      2 * self.baud_rate))
        m.submodules.symbols = symbols = shift_register.Down(10)
        m.submodules.in_edge = in_edge = edge.Detector(self.input)
        remaining = Signal(range(19 + 1))
        sample = timer.triggered & remaining[0]
        m.d.comb += self.start.eq(in_edge.fell & ~self.busy)
        m.d.comb += timer.reload.eq(self.start)
        m.d.comb += self.data.eq(symbols.word_out[1:-1])
        m.d.comb += symbols.bit_in.eq(self.input)
        m.d.comb += symbols.shift.eq(self.busy & sample)

        m.d.sync += self.done.eq(0)  # default
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += self.busy.eq(1)
                    m.d.sync += remaining.eq(19)
                    m.next = 'RUN'
            with m.State('RUN'):
                with m.If(timer.triggered):
                    m.d.sync += remaining.eq(remaining - 1)
                    with m.If(remaining == 1):
                        m.d.sync += self.busy.eq(0)
                        m.d.sync += self.done.eq(1)
                        m.next = 'IDLE'
        return m
