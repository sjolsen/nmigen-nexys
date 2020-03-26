"""Simple timer implementations."""

import numbers
from typing import Union

from nmigen import *
from nmigen.build import *

from nmigen_nexys.core import util


def _DivvyRational(q: numbers.Rational):
    assert isinstance(q, numbers.Rational)  # TODO: Real type-checking
    assert q >= 1
    result = [int(round(i * q)) for i in range(q.denominator)]
    assert len(set(result)) == len(result)
    return result


class DownTimer(Elaboratable):
    """Down-counting, self-reloading, free-running timer.

    The timer triggers at the end of the cycle.
    """

    def __init__(self, period: numbers.Rational):
        super().__init__()
        self.period = period
        self.reload = Signal(reset=0)
        self.counter = Signal(range(self.period.numerator),
                              reset=self.period.numerator - 1)
        self.triggered = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        triggers = _DivvyRational(self.period)
        m.d.comb += self.triggered.eq(
            util.Any(self.counter == t for t in triggers))
        with m.If(self.reload | (self.counter == 0)):
            m.d.sync += self.counter.eq(self.counter.reset)
        with m.Else():
            m.d.sync += self.counter.eq(self.counter - 1)
        return m


class UpTimer(Elaboratable):
    """Up-counting, self-reloading, free-running timer.

    The timer triggers at the end of the cycle.
    """

    def __init__(self, period: numbers.Rational):
        super().__init__()
        self.period = period
        self.reload = Signal(reset=0)
        self.counter = Signal(range(self.period.numerator), reset=0)
        self.triggered = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        triggers = [
            self.period.numerator - 1 - t for t in _DivvyRational(self.period)
        ]
        m.d.comb += self.triggered.eq(
            util.Any(self.counter == t for t in triggers))
        with m.If(self.reload | (self.counter == self.period.numerator - 1)):
            m.d.sync += self.counter.eq(self.counter.reset)
        with m.Else():
            m.d.sync += self.counter.eq(self.counter + 1)
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
        assert isinstance(period, (int, Signal))
        self.period = period
        self.go = Signal()
        self.running = Signal()
        self.triggered = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        if isinstance(self.period, int):
            assert self.period != 0
            period = Signal(range(self.period + 1), reset=self.period)
        elif isinstance(self.period, Signal):
            period = Signal(self.period.width)
            with m.If(self.go):
                m.d.sync += period.eq(self.period)
        else:
            raise TypeError(self.period)
        counter = Signal(period.width + 1)
        m.d.comb += self.running.eq(counter != 0)
        m.d.comb += self.triggered.eq(self.running & (counter == period))
        m.d.sync += counter.eq(
            Mux(self.running & ~self.triggered, counter + 1, 0))
        with m.If(self.go):
            m.d.sync += counter.eq(1)
        return m
