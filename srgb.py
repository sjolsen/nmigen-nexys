from nmigen import *
from nmigen.build import *

from lut import FunctionLUT, Rasterize


def sRGBGamma(u: float) -> float:
    if u <= 0.04045:
        return (25.0 * u) / 323.0
    else:
        return ((200.0 * u + 11.0) / 211.0)**(12.0 / 5.0)


def sRGBGammaLUT(input: Signal, output: Signal) -> FunctionLUT:
    gamma = Rasterize(
        sRGBGamma, umin=0.0, umax=1.0, xbits=input.width,
        vmin=0.0, vmax=1.0, ybits=output.width)
    return FunctionLUT(gamma, input, output)
