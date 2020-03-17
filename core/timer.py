from nmigen import *
from nmigen.build import *


class DownTimer(Elaboratable):

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.counter = Signal(range(self.period), reset=self.period - 1)
        self.triggered = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = self.counter
        m.d.comb += self.triggered.eq(counter == 0)
        m.d.sync += counter.eq(Mux(self.triggered, counter.reset, counter - 1))
        return m


class UpTimer(Elaboratable):

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.counter = Signal(range(self.period), reset=0)
        self.triggered = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = self.counter
        m.d.comb += self.triggered.eq(counter == self.period - 1)
        m.d.sync += counter.eq(Mux(self.triggered, counter.reset, counter + 1))
        return m
