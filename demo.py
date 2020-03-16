import math
from nmigen import *
from nmigen.build import *

from nexysa7100t import NexysA7100TPlatform
from lut import FunctionLUT, Rasterize
from pwm import PWM
from srgb import sRGBGammaLUT


class Timer(Elaboratable):

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.triggered = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = Signal(range(self.period), reset=self.period - 1)
        m.d.comb += self.triggered.eq(counter == 0)
        with m.If(counter == 0):
            m.d.sync += counter.eq(counter.reset)
        with m.Else():
            m.d.sync += counter.eq(counter - 1)
        return m


class TriangleWave(Elaboratable):

    def __init__(self, period: int, precision: int):
        super().__init__()
        self.period = period
        self.precision = precision
        self.output = Signal(precision)
        self.ascending = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = Signal(range(self.period), reset=0)
        m.d.sync += counter.eq(counter + 1)
        m.d.comb += self.ascending.eq(~counter[-1])
        high_bits = counter[-1 - self.precision : -1]
        with m.If(self.ascending):
            m.d.comb += self.output.eq(high_bits)
        with m.Else():
            m.d.comb += self.output.eq(C(-1, len(high_bits)) - high_bits)
        return m


class PositiveSineWave(Elaboratable):
    
    def __init__(self, twave: TriangleWave):
        super().__init__()
        self.twave = twave
        self.output = Signal(twave.precision)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        x = Signal(self.twave.output.width - 1)  # Two quarter-waves per half-wave
        y = Signal(self.output.width - 1)  # Output range is doubled by mirroring
        qwave = Rasterize(
            math.sin, umin=0.0, umax=math.pi / 2.0, xbits=x.width,
            vmin=0.0, vmax=1.0, ybits=y.width)
        m.submodules.qlut = qlut = FunctionLUT(qwave, x, y)
        xrev = Signal()
        yrev = Signal()
        m.d.comb += xrev.eq(self.twave.output[-1])
        m.d.comb += yrev.eq(~self.twave.ascending)
        m.d.comb += x.eq(Mux(xrev, C(-1, x.width) - self.twave.output[:-1], self.twave.output[:-1]))
        omid = C(2**(self.output.width - 1), self.output.width)
        m.d.comb += self.output.eq(Mux(yrev, omid - 1 - y, omid + y))
        return m


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        clk_period = int(platform.default_clk_frequency)
        m.submodules.timer = timer = Timer(clk_period // 2)
        m.submodules.triangle = triangle = TriangleWave(10 * clk_period, 8)
        m.submodules.sin = sin = PositiveSineWave(triangle)
        m.submodules.gamma = gamma = sRGBGammaLUT(sin.output, Signal(12))
        m.submodules.pwm = pwm = PWM(gamma.output)

        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        m.d.comb += anodes.eq(Repl(pwm.output, 8))

        shift_register = Signal(8, reset=0b11110000)
        with m.If(timer.triggered):
            m.d.sync += shift_register.eq(
                shift_register << 1 | shift_register >> 7)

        m.d.comb += segments.eq(shift_register)

        return m


if __name__ == "__main__":
    NexysA7100TPlatform().build(Demo(), do_program=True)