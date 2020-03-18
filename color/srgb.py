"""Definitions for https://en.wikipedia.org/wiki/SRGB."""

from nmigen import *

from nmigen_nexys.math import lut


def sRGBGamma(u: float) -> float:
    """Decoding gamma transformation."""
    if u <= 0.04045:
        return (25.0 * u) / 323.0
    else:
        return ((200.0 * u + 11.0) / 211.0)**(12.0 / 5.0)


def sRGBGammaLUT(input: Signal, output: Signal) -> lut.FunctionLUT:
    """Instantiate an sRGB gamma decoding LUT.
    
    The input and output signals are interpreted as varying linearly from 0 to
    1. The resolution of the input and output, which both affect the size of the
    LUT, are inferred from the width of the signals.
    """
    gamma = lut.Rasterize(
        sRGBGamma, umin=0.0, umax=1.0, xshape=input.shape(),
        vmin=0.0, vmax=1.0, yshape=output.shape())
    return lut.FunctionLUT(gamma, input, output)
