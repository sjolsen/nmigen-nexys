"""Simple demo for the Nexys A7-100T."""

from absl import app
from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.color import srgb
from nmigen_nexys.core import pwm as pwm_module
from nmigen_nexys.core import timer
from nmigen_nexys.core import top
from nmigen_nexys.math import trig


class Demo(Elaboratable):
    """Simple demo for the Nexys A7-100T.

    This demo displays a simple swirling pattern on each display in the
    seven-segment display bank. The brightness is smoothly ramped up and down.
    This demonstrates using PWM to modulate display brightness and a LUT to
    make the brightness perceptually uniform.
    """

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        clk_period = int(platform.default_clk_frequency)
        m.submodules.sin_timer = sin_timer = timer.UpTimer(
            clk_period * 10 // 256)
        m.submodules.sin = sin = trig.SineLUT(Signal(8), Signal(8))
        with m.If(sin_timer.triggered):
            m.d.sync += sin.input.eq(sin.input + 1)
        m.submodules.gamma = gamma = srgb.sRGBGammaLUT(sin.output, Signal(12))
        m.submodules.pwm = pwm = pwm_module.PWM(gamma.output)

        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        m.d.comb += anodes.eq(Repl(pwm.output, 8))

        m.submodules.shift_timer = shift_timer = timer.UpTimer(
            clk_period // 10)
        shift_register = Signal(6, reset=0b111100)
        with m.If(shift_timer.triggered):
            m.d.sync += shift_register.eq(
                shift_register << 1 | shift_register >> 5)

        m.d.comb += segments.eq(Cat(shift_register, C(0, 2)))

        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), Demo())

if __name__ == "__main__":
    app.run(main)
