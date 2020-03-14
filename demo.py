import itertools

from nexysa7100t import NexysA7100TPlatform
from nmigen import *
from nmigen.build import *


class Timer(Elaboratable):

    def __init__(self, reload: int):
        super().__init__()
        self._reload = reload
        self.triggered = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = Signal(range(self._reload + 1), reset=self._reload)
        m.d.comb += self.triggered.eq(counter == 0)
        with m.If(counter == 0):
            m.d.sync += counter.eq(counter.reset)
        with m.Else():
            m.d.sync += counter.eq(counter - 1)
        return m


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        clk_freq = platform.default_clk_frequency
        m.submodules.timer = timer = Timer(int(clk_freq // 2))

        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        m.d.comb += anodes.eq(0b11111111)  # Always on

        shift_register = Signal(8, reset=0b11110000)
        with m.If(timer.triggered):
            m.d.sync += shift_register.eq(
                shift_register << 1 | shift_register >> 7)

        m.d.comb += segments.eq(shift_register)

        return m


if __name__ == "__main__":
    NexysA7100TPlatform().build(Demo(), do_program=True)