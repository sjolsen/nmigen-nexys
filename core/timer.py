"""Simple timer implementations."""

from nmigen import *
from nmigen.build import *


class DownTimer(Elaboratable):
    """Down-counting, self-reloading, free-running timer.

    The timer triggers at the end of the cycle.
    """

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.counter = Signal(range(self.period), reset=self.period - 1)
        self.triggered = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        counter = self.counter
        m.d.comb += self.triggered.eq(counter == 0)
        m.d.sync += counter.eq(Mux(self.triggered, counter.reset, counter - 1))
        return m


class UpTimer(Elaboratable):
    """Up-counting, self-reloading, free-running timer.

    The timer triggers at the end of the cycle.
    """

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.counter = Signal(range(self.period), reset=0)
        self.triggered = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        counter = self.counter
        m.d.comb += self.triggered.eq(counter == self.period - 1)
        m.d.sync += counter.eq(Mux(self.triggered, counter.reset, counter + 1))
        return m
