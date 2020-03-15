from nmigen import *
from nmigen.build import *
from typing import Callable


class FunctionLUT(Elaboratable):

    def __init__(self, f: Callable[[int], int], input: Signal, output: Signal):
        super().__init__()
        self.input = input
        self.output = output
        if input.shape().signed:
            min_val = -(2**(input.shape().width - 1))
            max_val = 2**(input.shape().width - 1) - 1
        else:
            min_val = 0
            max_val = 2**input.shape().width - 1
        self.table = {x: f(x) for x in range(min_val, max_val + 1)}

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        with m.Switch(self.input):
            for x, y in sorted(self.table.items()):
                with m.Case(x):
                    m.d.comb += self.output.eq(y)
        return m