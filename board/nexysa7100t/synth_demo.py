from typing import Optional

from absl import app
from nmigen import *
from nmigen.build import *
from nmigen.lib.cdc import FFSynchronizer

from nmigen_nexys.audio import synth
from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.math import delta_sigma


class SynthDemoDriver(Elaboratable):

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        m.submodules.demo = demo = synth.Demo()
        go = platform.request('button_center')
        m.submodules.go_sync = FFSynchronizer(go, demo.start)
        rx = platform.request('uart', 0).rx
        m.submodules.rx_sync = FFSynchronizer(rx, demo.rx)
        audio = platform.request('audio', 0)
        # Pulse-density modulated output processed by on-board LPF
        m.submodules.pdm = pdm = delta_sigma.Modulator(demo.pcm_output.width)
        m.d.comb += pdm.input.eq(demo.pcm_output)
        m.d.comb += audio.pwm.eq(pdm.output)
        m.d.comb += audio.sd.eq(0)  # No shutdown
        leds = Cat(*[platform.request('led', i) for i in range(16)])
        m.d.comb += leds.eq(demo.channel_indicators)
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), SynthDemoDriver())

if __name__ == "__main__":
    app.run(main)
