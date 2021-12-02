from typing import Optional

from nmigen import *
from nmigen.build import *

from nmigen_nexys.core import util


class Modulator(Elaboratable):

    def __init__(self, width: int):
        super().__init__()
        self.width = width
        self.input = Signal(signed(width))
        self.output = Signal()

    def elaborate(self, _: Optional[Platform]) -> Module:
        m = Module()
        # The integrator can be modeled by an infinite sequence S(n):
        #
        #   S(0) = 0
        #   S(n + 1) = S(n) + X(n + 1) - Y(n)
        #
        # where X(n) is the input on cycle n and Y(n) is the value encoded by
        # the single-bit output of the modulator, given by:
        #
        #   Y(n) = {  2**(N - 1) - 1    if S(n) ≥ 0;
        #            -2**(N - 1)        otherwise    }
        #
        # If X is an N-bit two's-complement signed input where N ≥ 1, then N + 1
        # bits are sufficient to encode the signed integrator and the
        # intermediate values when computed in the order suggested by the
        # parenthesized expression:
        #
        #   S(n + 1) = (S(n) - Y(n)) + X(n + 1)
        #
        # That is to say, P0 holds and P(n) holds for all n, where:
        #
        #   P0 = S(0) ∈ [-2**N, 2**N); and
        #   P(n) = (S(n) - Y(n)) ∈ [-2**N, 2**N)
        #        ∧ (S(n + 1)     ∈ [-2**N, 2**N).
        #
        # Clearly S(0) = 0 is representable as a two's-complement signed integer
        # of any size. P can then be proved inductively. First, for P(0):
        #
        #   1. S(0) - Y(0)
        #        = 0 - (2**(N - 1) - 1)  # By definition of S and Y
        #        = -2**(N - 1) + 1
        #        ∈ [-2**N, 2**N);
        #   2. S(0 + 1)
        #        = (S(0) - Y(0)) + X(1)             # By definition of S
        #        = -2**(N - 1) + 1 + X(1)           # Substituting intermediate result from (1)
        #        ∈ [-2**(N - 1) + 1 + -2**(N - 1),
        #           -2**(N - 1) + 1 +  2**(N - 1))  # X is an N-bit signed integer
        #        = [-2**N + 1, 1)
        #        ⊆ [-2**N, 2**N).                   # 2**N ≥ 2
        #
        # Second, assuming P(n) we prove P(n + 1):
        #
        #   a) If S(n + 1) ≥ 0, then:
        #     1. S(n + 1) - Y(n + 1)
        #          = S(n + 1) - (2**(N - 1) - 1)        # By definition of Y and assumption (a)
        #          ∈ [0 - 2**(N - 1) + 1,               # By assumption (a)
        #             2**N - 2**(N - 1) + 1)            # By I.H. P(n)
        #          = [-2**(N - 1) + 1, 2**(N - 1) + 1)
        #          ⊆ [-2**N, 2**(N - 1) + 2**(N - 1))   # 2**(N - 1) ≥ 1
        #          ⊆ [-2**N, 2**N);
        #     2. S((n + 1) + 1)
        #          = (S(n + 1) - Y(n + 1)) + X(n + 2)    # By definition of S
        #          ∈ [-2**(N - 1) + 1 + -2**(N - 1),     # Substituting intermediate result from (1)
        #              2**(N - 1) + 1 + 2**(N - 1) - 1)  # (note: final -1 term comes from addition of half-open ranges)
        #          = [-2**N + 1, 2**N)
        #          ⊆ [-2**N, 2**N).
        #   b) otherwise:
        #     1. S(n + 1) - Y(n + 1)
        #          = S(n + 1) - -2**(N - 1)     # By definition of Y and assumption (b)
        #          ∈ [-2**N + 2**(N - 1),       # By I.H. P(n)
        #             2**(N - 1))               # By assumption (b)
        #          = [-2**(N - 1), 2**(N - 1))
        #          ⊆ [-2**N, 2**N);
        #     2. S((n + 1) + 1)
        #          = (S(n + 1) - Y(n + 1)) + X(n + 2)  # By definition of S
        #          ∈ [-2**(N - 1) + -2**(N - 1),       # Substituting intermediate result from (1)
        #              2**(N - 1) + 2**(N - 1) - 1)    # (note: final -1 term comes from addition of half-open ranges)
        #          = [-2**N, 2**N - 1)
        #          ⊆ [-2**N, 2**N).
        #
        # From P(0) and P(n) → P(n + 1) we have ∀n∈𝐍.P(n) by induction.
        shape = signed(self.width + 1)
        X = Signal(shape)
        Y = Signal(shape)
        Y_min = C(util.ShapeMin(self.input.shape()), shape)
        Y_max = C(util.ShapeMax(self.input.shape()), shape)
        S = Signal(shape, reset=0)
        m.d.comb += [
            self.output.eq(S >= 0),
            X.eq(self.input),
            Y.eq(Mux(self.output, Y_max, Y_min)),
        ]
        m.d.sync += S.eq((S - Y) + X)
        return m
