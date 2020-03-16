import functools
from nmigen import *
from nmigen.build import *
from typing import Callable


def ShapeMin(s: Shape) -> int:
    return -(2**(s.width - 1)) if s.signed else 0


def ShapeMax(s: Shape) -> int:
    return 2**(s.width - 1) - 1 if s.signed else 2**s.width - 1


def ShapeMid(s: Shape) -> int:
    return 0 if s.signed else 2**(s.width - 1)


def Clamp(x: float, shape: Shape) -> int:
    y = int(round(x))
    y = max(y, ShapeMin(shape))
    y = min(y, ShapeMax(shape))
    return y


def LinearTransformation(imin: float, imax: float,
                         omin: float, omax: float) -> Callable[[float], float]:
    # https://en.wikipedia.org/wiki/Linear_equation:
    #   y - y1 = ((y2 - y1) / (x2 - x1)) * (x - x1)
    def f(x):
        return float(x - imin) * float(omax - omin) / float(imax - imin) + omin
    return f


def Rasterize(f: Callable[[float], float],
              umin: float, umax: float, xshape: Shape,
              vmin: float, vmax: float, yshape: Shape) -> Callable[[int], int]:
    u_x = LinearTransformation(
        imin=ShapeMin(xshape), imax=ShapeMax(xshape), omin=umin, omax=umax)
    y_v = LinearTransformation(
        imin=vmin, imax=vmax, omin=ShapeMin(yshape), omax=ShapeMax(yshape))
    @functools.wraps(f)
    def rasterized(x: int) -> int:
        u = u_x(float(x))
        v = f(u)
        y = y_v(v)
        # Clamp to range of y so floating-point imprecision can't cause wrap-
        # around
        return Clamp(y, yshape)
    return rasterized


class FunctionLUT(Elaboratable):

    def __init__(self, f: Callable[[int], int], input: Signal, output: Signal):
        super().__init__()
        self.input = input
        self.output = output
        min_val = ShapeMin(input.shape())
        max_val = ShapeMax(input.shape())
        self.table = {x: f(x) for x in range(min_val, max_val + 1)}

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        with m.Switch(self.input):
            for x, y in sorted(self.table.items()):
                with m.Case(x):
                    m.d.comb += self.output.eq(y)
        return m