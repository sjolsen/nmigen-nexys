"""Tools for building lookup tables (LUTs)."""

import functools
from typing import Callable

from nmigen import *
from nmigen.build import *

from nmigen_nexys.core import util


def LinearTransformation(
        imin: float, imax: float,
        omin: float, omax: float) -> Callable[[float], float]:
    """Build a linear transformation using the two-point equation."""
    # https://en.wikipedia.org/wiki/Linear_equation:
    #   y - y1 = ((y2 - y1) / (x2 - x1)) * (x - x1)
    def f(x):
        return float(x - imin) * float(omax - omin) / float(imax - imin) + omin
    return f


def Rasterize(
        f: Callable[[float], float],
        umin: float, umax: float, xshape: Shape,
        vmin: float, vmax: float, yshape: Shape) -> Callable[[int], int]:
    """Rasterize an arbitrary floating-point-domain function.

    This converts a function acting on floats to a form suitable for use with
    FunctionLUT. The resulting integer-domain function is intended to be used
    with a domain and range spanning the representable range of xshape and
    yshape, respectively. This is linearly mapped to the domain and range
    of f specified by [umin, umax] and [vmin, vmax], respectively.
    """
    u_x = LinearTransformation(
        imin=util.ShapeMin(xshape), imax=util.ShapeMax(xshape) + 1,
        omin=umin, omax=umax)
    y_v = LinearTransformation(
        imin=vmin, imax=vmax,
        omin=util.ShapeMin(yshape), omax=util.ShapeMax(yshape) + 1)

    @functools.wraps(f)
    def rasterized(x: int) -> int:
        u = u_x(float(x))
        v = f(u)
        y = y_v(v)
        # Clamp to range of y so floating-point imprecision can't cause wrap-
        # around
        return util.Clamp(y, yshape)
    return rasterized


class FunctionLUT(Elaboratable):
    """Build a LUT from a function.

    The width of the input and output are inferred from the input and output
    signals. The function is tabulated at compile time and is available through
    the compile-time table dictionary as well as the run-time signals.
    """

    def __init__(self, f: Callable[[int], int], input: Signal, output: Signal):
        super().__init__()
        self.input = input
        self.output = output
        min_val = util.ShapeMin(input.shape())
        max_val = util.ShapeMax(input.shape())
        self.table = {x: f(x) for x in range(min_val, max_val + 1)}

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        with m.Switch(self.input):
            for x, y in sorted(self.table.items()):
                with m.Case(x):
                    m.d.comb += self.output.eq(y)
        return m
