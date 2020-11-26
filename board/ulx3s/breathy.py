"""Simple demo for the ULX3S (85F variant)."""

import itertools
from typing import List

from absl import app
from nmigen import *
from nmigen.build import *
from nmigen_boards import ulx3s

from nmigen_nexys.bazel import top
from nmigen_nexys.color import srgb
from nmigen_nexys.core import pwm as pwm_module
from nmigen_nexys.core import timer
from nmigen_nexys.math import trig


def get_leds(platform: Platform) -> List[Resource]:

    def get_all_resources(name):
        resources = []
        for number in itertools.count():
            try:
                resources.append(platform.request(name, number))
            except ResourceError:
                break
        return resources

    rgb_leds = [res for res in get_all_resources("rgb_led")]
    leds     = [res.o for res in get_all_resources("led")]
    leds.extend([led.r.o for led in rgb_leds])
    leds.extend([led.g.o for led in rgb_leds])
    leds.extend([led.b.o for led in rgb_leds])
    return leds


class Blinky(Elaboratable):

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

        leds = get_leds(platform)
        m.d.comb += Cat(leds).eq(Repl(pwm.output, len(leds)))

        return m


def main(_):
    top.build(ulx3s.ULX3S_85F_Platform(), Blinky())

if __name__ == "__main__":
    app.run(main)
