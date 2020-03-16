import functools
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


def Rasterize(f: Callable[[float], float],
              umin: float, umax: float, xbits: int,
              vmin: float, vmax: float, ybits: int) -> Callable[[int], int]:
    @functools.wraps(f)
    def rasterized(x: int) -> int:
        # u(x) = m * x + b
        # u(0) = umin
        # u(2**xbits - 1) = umax
        # umin = m * 0 + b
        #   => b = umin
        # umax = m * (2**xbits - 1) + b
        #   => m = (umax - umin) / (2**xbits - 1)
        # u(x) = x * (umax - umin) / (2**xbits - 1) + umin
        u = float(x * (umax - umin)) / float((2**xbits - 1) + umin)
        v = f(u)
        # y(v) = m * v + b
        # y(vmin) = 0
        # y(vmax) = 2**ybits - 1
        # 0 = m * vmin + b
        #   => b = -m * vmin
        # 2**ybits - 1 = m * vmax + b
        #   => b = 2**ybits - 1 - m * vmax
        # -m * vmin = 2**ybits - 1 - m * vmax
        #   => m * vmax - m * vmin = 2**ybits - 1
        #   => m * (vmax - vmin) = 2**ybits - 1
        #   => m = (2**ybits - 1) / (vmax - vmin)
        # b = -m * vmin
        #   => y(v) = m * v - m * vmin
        #   => y(v) = (v - vmin) * (2**ybits - 1) / (vmax - vmin)
        y = float(v - vmin) * float(2**ybits - 1) / float(vmax - vmin)
        # Clamp to range of y so floating-point imprecision can't cause wrap-
        # around
        y = int(round(y))
        y = max(y, 0)
        y = min(y, 2**ybits - 1)
        return y
    return rasterized