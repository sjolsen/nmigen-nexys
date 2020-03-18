"""Square a fixed-point number in the range [0, 1)."""

from nmigen import *
from nmigen.build import *


class SquareFraction(Elaboratable):
    """Square a fixed-point number in the range [0, 1).

    This class was originally conceived as a simple-to-compute alternative to
    a more precise gamma function for PWM brightness. It interprets its input as
    a fraction-only fixed-point number and squares it.
    """

    def __init__(self, input: Signal):
        super().__init__()
        self.input = input
        self.widened = Signal(2 * input.width)
        self.squared = Signal(2 * input.width)
        self.output = self.narrowed = Signal(input.width)

    @property
    def ports(self):
        """Signals used by the test bed."""
        return ('input', 'widened', 'squared', 'output')

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.d.comb += self.widened.eq(Cat(self.input, C(0, self.input.width)))
        m.d.comb += self.squared.eq(self.widened * self.widened)
        m.d.comb += self.narrowed.eq(self.squared[self.input.width:])
        return m
