"""Implementations of linear feedback shift registers (LFSRs)."""

import functools
import operator
from typing import List

from nmigen import *
from nmigen.build import *

from nmigen_nexys.core import shift_register


class Fibonacci(Elaboratable):
    """An LFSR as described by https://en.wikipedia.org/wiki/Linear-feedback_shift_register#Fibonacci_LFSRs.

    Args:
        polynomial: The feedback polynomial expressed as a list of exponents.
                    Must include zero (x^0 = 1). For example, the polynomial
                    given in the Wikipedia example,
                    x^16 + x^14 + x^13 + x^11 + 1, would be expressed as:

            [16, 14, 13, 11, 0]

        seed: The initial shift register contents.
    """

    def __init__(self, polynomial: List[int], seed: int):
        super().__init__()
        unique = set(polynomial)
        assert 0 in unique
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
        taps = [register.word_out[i - 1] for i in self.polynomial if i != 0]
        feedback = functools.reduce(operator.xor, taps)
        m.d.comb += register.bit_in.eq(feedback)
        m.d.comb += register.shift.eq(1)
        m.d.comb += self.state.eq(register.word_out)
        m.d.comb += self.output.eq(register.bit_out)
        return m
