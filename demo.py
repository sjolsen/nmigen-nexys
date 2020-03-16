from nmigen import *
from nmigen.build import *

from nexysa7100t import NexysA7100TPlatform
from pwm import PWM
from srgb import sRGBGammaLUT
from timer import UpTimer
from trig import SineLUT


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        clk_period = int(platform.default_clk_frequency)
        m.submodules.sin_timer = sin_timer = UpTimer(clk_period * 10 // 256)
        m.submodules.sin = sin = SineLUT(Signal(8), Signal(8))
        with m.If(sin_timer.triggered):
            m.d.sync += sin.input.eq(sin.input + 1)
        m.submodules.gamma = gamma = sRGBGammaLUT(sin.output, Signal(12))
        m.submodules.pwm = pwm = PWM(gamma.output)

        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        m.d.comb += anodes.eq(Repl(pwm.output, 8))

        m.submodules.shift_timer = shift_timer = UpTimer(clk_period // 10)
        shift_register = Signal(6, reset=0b111100)
        with m.If(shift_timer.triggered):
            m.d.sync += shift_register.eq(
                shift_register << 1 | shift_register >> 5)

        m.d.comb += segments.eq(Cat(shift_register, C(0, 2)))

        return m


if __name__ == "__main__":
    NexysA7100TPlatform().build(Demo(), do_program=True)