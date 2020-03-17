import math

from nmigen import *
from nmigen.build import *

from nmigen_nexys.core import util
from nmigen_nexys.math import lut


class SineLUT(Elaboratable):
    
    def __init__(self, input: Signal, output: Signal):
        super().__init__()
        self.input = input
        self.output = output

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        x = Signal(self.input.width - 2)  # Four (2**2) quarter-waves
        y = Signal(self.output.width - 1)  # Output range is doubled by mirroring
        qwave = lut.Rasterize(
            math.sin, umin=0.0, umax=math.pi / 2.0, xshape=x.shape(),
            vmin=0.0, vmax=1.0, yshape=y.shape())
        m.submodules.qlut = lut.FunctionLUT(qwave, x, y)
        hparity = self.input[-2]
        with m.If(hparity):
            m.d.comb += x.eq(-self.input[:-2])  # Implicit mod pi/2
        with m.Else():
            m.d.comb += x.eq(self.input[:-2])
        # Because 2**x.width is not representable, there's a discontinuity at
        # the peaks and troughs. Handle that outside the LUT.
        xdiscontinuity = hparity & (self.input[:-2] == 0)
        vparity = self.input[-1]  # Works for both signed and unsigned
        vmid = util.ShapeMid(self.output.shape())
        with m.If(vparity):
            with m.If(xdiscontinuity):
                m.d.comb += self.output.eq(util.ShapeMin(self.output.shape()))
            with m.Else():
                m.d.comb += self.output.eq(vmid - y)
        with m.Else():
            with m.If(xdiscontinuity):
                m.d.comb += self.output.eq(util.ShapeMax(self.output.shape()))
            with m.Else():
                m.d.comb += self.output.eq(vmid + y)
        return m


class CosineLUT(Elaboratable):
    
    def __init__(self, input: Signal, output: Signal):
        super().__init__()
        self.input = input
        self.output = output

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        shifted = Signal(self.input.shape())
        m.submodules.sin = SineLUT(shifted, self.output)
        m.d.comb += shifted.eq(self.input + 2**(self.input.width - 2))
        return m
