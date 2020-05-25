import fractions

from absl import app
from nmigen import *
from nmigen.build import *

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import timer
from nmigen_nexys.core import util
from nmigen_nexys.math import delta_sigma


A4 = 440
C4 = A4 / 2**(9/12)
E4 = A4 / 2**(5/12)
G4 = A4 / 2**(2/12)


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        synths = []
        for i, freq in enumerate([C4, E4, G4]):
            switch = platform.request('switch', i)
            freq_timer = timer.DownTimer(period=util.GetClockFreq(platform) / (2**12 * freq))
            m.submodules += freq_timer
            synth = Signal(signed(12))
            with m.If(freq_timer.triggered):
                m.d.sync += synth.eq(synth + 1)
            masked = Signal(signed(16))
            m.d.comb += masked.eq(Mux(switch, synth >> 4, 0))
            synths.append(masked)
        # Sample at 44.1 kHz
        m.submodules.sample_timer = sample_timer = timer.DownTimer(
            period=fractions.Fraction(util.GetClockFreq(platform), 44_100))
        sample = Signal(signed(16))
        with m.If(sample_timer.triggered):
            m.d.sync += sample.eq(sum(synths))
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
