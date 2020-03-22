import functools
import operator
from typing import List

from nmigen import *
from nmigen.build import *

from nmigen_nexys.core import shift_register


class Fibonacci(Elaboratable):

    def __init__(self, polynomial: List[int], seed: int):
        super().__init__()
        unique = set(polynomial)
        assert 1 in unique
        assert len(polynomial) == len(unique)
        order = max(polynomial)
        assert order > 1
        assert 0 < seed < 2**order
        self.order = order
        self.polynomial = polynomial
        self.seed = seed
        self.state = Signal(order)
        self.output = Signal()

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.submodules.register = register = shift_register.Up(self.order,
                                                             reset=self.seed)
        taps = [register.word_out[i - 1] for i in self.polynomial if i != 1]
        feedback = functools.reduce(operator.xor, taps)
        m.d.comb += register.bit_in.eq(feedback)
        m.d.comb += register.shift.eq(1)
        m.d.comb += self.state.eq(register.word_out)
        m.d.comb += self.output.eq(register.bit_out)
        return m
