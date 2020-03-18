from nmigen import *
from nmigen.build import *


class Detector(Elaboratable):

    def __init__(self, input: Signal):
        super().__init__()
        assert input.width == 1
        self.input = input
        self.rose = Signal()
        self.fell = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        last = Signal()
        m.d.sync += last.eq(self.input)
        m.d.comb += self.rose.eq(self.input & ~last)
        m.d.comb += self.fell.eq(~self.input & last)
        return m
