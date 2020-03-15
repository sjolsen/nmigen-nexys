from nmigen import *
from nmigen.build import *

from lut import FunctionLUT


def sRGBGamma(u: float) -> float:
    if u <= 0.04045:
        return (25.0 * u) / 323.0
    else:
        return ((200.0 * u + 11.0) / 211.0)**(12.0 / 5.0)


def sRGBGammaU8(x: int) -> int:
    u = float(x) / 256.0
    v = sRGBGamma(u)
    y = int(round(v * 256.0))
    return y


def sRGBGammaU8LUT(input: Signal, output: Signal) -> FunctionLUT:
    return FunctionLUT(sRGBGammaU8, input, output)
