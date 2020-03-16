import math
from nmigen import *
from nmigen.build import *

from nexysa7100t import NexysA7100TPlatform
from lut import FunctionLUT, Rasterize, ShapeMid
from pwm import PWM
from srgb import sRGBGammaLUT
from timer import UpTimer


class SineLUT(Elaboratable):
    
    def __init__(self, input: Signal, output: Signal):
        super().__init__()
        self.input = input
        self.output = output

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        x = Signal(self.input.width - 2)  # Four (2**2) quarter-waves
        y = Signal(self.output.width - 1)  # Output range is doubled by mirroring
        qwave = Rasterize(
            math.sin, umin=0.0, umax=math.pi / 2.0, xshape=x.shape(),
            vmin=0.0, vmax=1.0, yshape=y.shape())
        m.submodules.qlut = FunctionLUT(qwave, x, y)
        hparity = self.input[-2]
        with m.If(hparity):
            m.d.comb += x.eq(-1 - self.input[:-2])  # Implicit mod pi/2
        with m.Else():
            m.d.comb += x.eq(self.input[:-2])
        vparity = self.input[-1]  # Works for both signed and unsigned
        vmid = ShapeMid(self.output.shape())
        with m.If(vparity):
            m.d.comb += self.output.eq(vmid - 1 - y)
        with m.Else():
            m.d.comb += self.output.eq(vmid + y)
        return m


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        clk_period = int(platform.default_clk_frequency)
        m.submodules.sin_timer = sin_timer = UpTimer(clk_period * 10)
        m.submodules.sin = sin = SineLUT(Signal(8), Signal(8))
        m.d.comb += sin.input.eq(sin_timer.counter[-8:])
        m.submodules.gamma = gamma = sRGBGammaLUT(sin.output, Signal(12))
        m.submodules.pwm = pwm = PWM(gamma.output)

        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        m.d.comb += anodes.eq(Repl(pwm.output, 8))

        m.submodules.shift_timer = shift_timer = UpTimer(clk_period // 2)
        shift_register = Signal(8, reset=0b11110000)
        with m.If(shift_timer.triggered):
            m.d.sync += shift_register.eq(
                shift_register << 1 | shift_register >> 7)

        m.d.comb += segments.eq(shift_register)

        return m


if __name__ == "__main__":
    NexysA7100TPlatform().build(Demo(), do_program=True)