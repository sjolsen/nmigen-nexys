"""Common tools for pulse-width modulation (PWM)."""

from nmigen import *
from nmigen.build import *


class PWM(Elaboratable):
    """Simple PWM implementation.

    The period of the PWM output is ``2**duty_cycle.width`` cycles. The strobe
    signal strobes at the beginning of the PWM cycle.
    """

    def __init__(self, duty_cycle: Signal):
        super().__init__()
        self.duty_cycle = duty_cycle
        self.strobe = Signal()
        self.output = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        counter = Signal(self.duty_cycle.width, reset=0)
        m.d.sync += counter.eq(counter + 1)
        m.d.comb += self.strobe.eq(counter ==
                                   C(2**counter.width - 1, counter.width))
        m.d.comb += self.output.eq(counter < self.duty_cycle)
        return m
