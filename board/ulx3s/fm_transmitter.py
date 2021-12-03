"""Simple demo for the ULX3S (85F variant)."""

from absl import app
from nmigen import *
from nmigen.build import *
from nmigen_boards import ulx3s

from nmigen_nexys.bazel import top
from nmigen_nexys.board.ulx3s import fm
from nmigen_nexys.core import timer
from nmigen_nexys.core import util
from nmigen_nexys.math import trig


class ToneGenerator(Elaboratable):

    def __init__(self, *, freq_Hz: int, pcm_depth: int):
        super().__init__()
        self.freq_Hz = freq_Hz
        self.pcm_depth = pcm_depth
        self.pcm = Signal(signed(pcm_depth))

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        clk_freq = util.GetClockFreq(platform)

        phase = Signal(unsigned(8))
        m.submodules.sin = sin = trig.SineLUT(phase, self.pcm)
        m.submodules.sin_timer = sin_timer = timer.UpTimer(
            clk_freq // (self.freq_Hz * 2**phase.width))
        with m.If(sin_timer.triggered):
            m.d.sync += phase.eq(phase + 1)

        return m


class Transmitter(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        m.submodules.tone = tone = ToneGenerator(freq_Hz=440, pcm_depth=16)
        m.submodules.transmitter = transmitter = fm.Transmitter(
            pcm_depth=tone.pcm.width)
        m.d.comb += transmitter.pcm.eq(tone.pcm)
        return m


def main(_):
    top.build(ulx3s.ULX3S_85F_Platform(), Transmitter())

if __name__ == "__main__":
    app.run(main)
