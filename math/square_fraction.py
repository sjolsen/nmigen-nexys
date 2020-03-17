from nmigen import *
from nmigen.build import *


class SquareFraction(Elaboratable):

    def __init__(self, input: Signal):
        super().__init__()
        self.input = input
        self.widened = Signal(2 * input.width)
        self.squared = Signal(2 * input.width)
        self.output = self.narrowed = Signal(input.width)

    @property
    def ports(self):
        return ('input', 'widened', 'squared', 'output')

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        m.d.comb += self.widened.eq(Cat(self.input, C(0, self.input.width)))
        m.d.comb += self.squared.eq(self.widened * self.widened)
        m.d.comb += self.narrowed.eq(self.squared[self.input.width:])
        return m
