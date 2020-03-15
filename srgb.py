from nmigen import *
from nmigen.build import *

from lut import FunctionLUT


def sRGBGamma(u: float) -> float:
    if u <= 0.04045:
        return (25.0 * u) / 323.0
    else:
        return ((200.0 * u + 11.0) / 211.0)**(12.0 / 5.0)


def sRGBGammaInt(xbits: int, ybits: int, x: int) -> int:
    u = float(x) / float(2**xbits)
    v = sRGBGamma(u)
    y = int(round(v * float(2**ybits)))
    return y


def sRGBGammaLUT(input: Signal, output: Signal) -> FunctionLUT:
    f = lambda x: sRGBGammaInt(input.width, output.width, x)
    return FunctionLUT(f, input, output)
