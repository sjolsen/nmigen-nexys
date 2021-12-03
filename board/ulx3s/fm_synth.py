"""Synthesizer broadcasting on FM."""

from absl import app
from nmigen import *
from nmigen.build import *
from nmigen.lib.cdc import FFSynchronizer
from nmigen_boards import ulx3s

from nmigen_nexys.audio import synth
from nmigen_nexys.bazel import top
from nmigen_nexys.board.ulx3s import fm


class Transmitter(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        m.submodules.demo = demo = synth.Demo()
        go = platform.request('button_pwr')
        m.submodules.go_sync = FFSynchronizer(go, demo.start)
        m.submodules.transmitter = transmitter = fm.Transmitter(
            pcm_depth=demo.pcm_output.width)
        m.d.comb += transmitter.pcm.eq(demo.pcm_output)
        return m


def main(_):
    top.build(ulx3s.ULX3S_85F_Platform(), Transmitter())

if __name__ == "__main__":
    app.run(main)
