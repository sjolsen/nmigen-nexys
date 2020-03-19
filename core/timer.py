"""Simple timer implementations."""

from typing import Union

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


class OneShot(Elaboratable):
    r"""Single-shot, resettable timer.

    The timer will trigger period cycles after the cycle in which go is set. If
    for instance period is 1, the timer will trigger the cycle after go is set.

                     period = 1             period = 2
                   __    __    __         __    __    __
      clk       __/  \__/  \__/  \__   __/  \__/  \__/  \__
                   __                     __
      go        __/  \______________   __/  \______________
                         __                           __
      triggered ________/  \________   ______________/  \__

                  |- 1 -|                |---- 2 ----|

    In this way, the period is made to be the measure between the leading edges
    of go and triggered. If triggered were fed back to go, the timer would
    trigger continuously with the correct period.

    If go is strobed again before the timer expires, it will restart the timer.
    """

    def __init__(self, period: Union[int, Signal]):
        super().__init__()
        self.period = period
        self.go = Signal()
        self.running = Signal()
        self.triggered = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        if isinstance(self.period, int):
            period = Signal(range(self.period + 1), reset=self.period)
        elif isinstance(self.period, Signal):
            period = Signal(self.period.width)
            with m.If(self.go):
                m.d.sync += period.eq(self.period)
        else:
            raise TypeError(self.period)
        counter = Signal(period.width + 1)
        m.d.comb += self.running.eq(counter != 0)
        with m.If(period != 0):
            m.d.comb += self.triggered.eq(counter == period)
            m.d.sync += counter.eq(Mux(self.triggered, 0, counter + 1))
            with m.If(self.go):
                m.d.sync += counter.eq(1)
        return m
