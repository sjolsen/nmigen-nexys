import fractions

from absl import app
from nmigen import *
from nmigen.build import *

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import timer
from nmigen_nexys.core import util
from nmigen_nexys.math import delta_sigma
from nmigen_nexys.math import trig


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        synths = []
        synth_en = []
        for i in range(16):
            freq = 220 * 2**((15 - i) / 12)
            switch = platform.request('switch', i)
            led = platform.request('led', i)
            freq_timer = timer.DownTimer(period=util.GetClockFreq(platform) / (2**12 * freq))
            m.submodules += freq_timer
            synth = Signal(12)
            with m.If(freq_timer.triggered):
                m.d.sync += synth.eq(synth + 1)
            synths.append(synth)
            synth_en.append(switch)
            m.d.comb += led.eq(switch)
        # Sample at 44.1 kHz
        m.submodules.sample_timer = sample_timer = timer.DownTimer(
            period=fractions.Fraction(util.GetClockFreq(platform), 44_100))
        sample = Signal(signed(16))
        # Share a LUT
        m.submodules.sine = sine = trig.SineLUT(Signal(12), Signal(signed(12)))
        next_sample = Signal.like(sample)
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(sample_timer.triggered):
                    m.d.sync += next_sample.eq(0)
                    m.next = 'SAMPLE0'
            for i, synth in enumerate(synths):
                with m.State(f'SAMPLE{i}'):
                    m.d.comb += sine.input.eq(synth)
                    with m.If(synth_en[i]):
                        m.d.sync += next_sample.eq(next_sample + sine.output)
                    if i + 1 == len(synths):
                        m.next = 'DONE'
                    else:
                        m.next = f'SAMPLE{i + 1}'
            with m.State('DONE'):
                m.d.sync += sample.eq(next_sample)
                m.next = 'IDLE'
        m.submodules.pdm = pdm = delta_sigma.Modulator(sample.width)
        m.d.comb += pdm.input.eq(sample)
        audio = platform.request('audio', 0)
        m.d.comb += audio.pwm.eq(pdm.output)
        m.d.comb += audio.sd.eq(0)  # No shutdown
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), Demo())

if __name__ == "__main__":
    app.run(main)
