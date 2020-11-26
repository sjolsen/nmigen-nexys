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
        m.submodules.sin = sin = trig.SineLUT(Signal(8), Signal(8))
        m.submodules.gamma = gamma = srgb.sRGBGammaLUT(sin.output, Signal(12))

        leds = get_leds(platform)
        phases = []
        pwms = []
        for i, led in enumerate(leds):
            phase = Signal(8, reset=round(256 * (i / len(leds))))
            phases.append(phase)
            pwm = pwm_module.PWM(Signal(gamma.output.shape(), name='duty_cycle'))
            pwms.append(pwm)
            m.d.comb += led.eq(pwm.output)
        m.submodules += pwms

        m.submodules.sin_timer = sin_timer = timer.UpTimer(
            clk_period * 5 // 256)
        with m.If(sin_timer.triggered):
            for phase in phases:
                m.d.sync += phase.eq(phase + 1)

        m.d.sync += sin.input.eq(phases[0])
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(sin_timer.triggered):
                    m.next = 'UPDATE_0'
            for i, pwm in enumerate(pwms):
                with m.State(f'UPDATE_{i}'):
                    m.d.sync += pwm.duty_cycle.eq(gamma.output)
                    if i < len(leds) - 1:
                        m.d.sync += sin.input.eq(phases[i + 1])
                        m.next = f'UPDATE_{i + 1}'
                    else:
                        m.next = 'IDLE'

        return m


def main(_):
    top.build(ulx3s.ULX3S_85F_Platform(), Blinky())

if __name__ == "__main__":
    app.run(main)
