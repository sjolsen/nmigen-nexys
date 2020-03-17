from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.color import srgb
from nmigen_nexys.core import pwm as pwm_module
from nmigen_nexys.core import timer
from nmigen_nexys.math import trig


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        clk_period = int(platform.default_clk_frequency)
        m.submodules.sin_timer = sin_timer = timer.UpTimer(clk_period * 10 // 256)
        m.submodules.sin = sin = trig.SineLUT(Signal(8), Signal(8))
        with m.If(sin_timer.triggered):
            m.d.sync += sin.input.eq(sin.input + 1)
        m.submodules.gamma = gamma = srgb.sRGBGammaLUT(sin.output, Signal(12))
        m.submodules.pwm = pwm = pwm_module.PWM(gamma.output)

        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        m.d.comb += anodes.eq(Repl(pwm.output, 8))

        m.submodules.shift_timer = shift_timer = timer.UpTimer(clk_period // 10)
        shift_register = Signal(6, reset=0b111100)
        with m.If(shift_timer.triggered):
            m.d.sync += shift_register.eq(
                shift_register << 1 | shift_register >> 5)

        m.d.comb += segments.eq(Cat(shift_register, C(0, 2)))

        return m


if __name__ == "__main__":
    nexysa7100t.NexysA7100TPlatform().build(Demo(), do_program=True)
