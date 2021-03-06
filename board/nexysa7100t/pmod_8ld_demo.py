"""Demo for https://store.digilentinc.com/pmod-8ld-eight-high-brightness-leds/."""

from absl import app
from nmigen import *
from nmigen.build import *

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.pmod import pmod_8ld


class Demo(Elaboratable):
    """Demo for the Digilent Pmod 8LD.

    This demo assumes there are two modules plugged into JA and JB. It displays
    a point bouncing back and forth across the two modules.
    """

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        clk_period = int(platform.default_clk_frequency)
        m.submodules.timer = timer = timer_module.UpTimer(clk_period // 10)

        pmod0 = platform.request('pmod_8ld', 0)
        pmod1 = platform.request('pmod_8ld', 1)
        snake = Signal(16, reset=1)
        snake_up = Signal()
        with m.If(timer.triggered):
            with m.Switch(snake):
                with m.Case(0x0001):
                    m.d.sync += snake.eq(snake << 1)
                    m.d.sync += snake_up.eq(1)
                with m.Case(0x8000):
                    m.d.sync += snake.eq(snake >> 1)
                    m.d.sync += snake_up.eq(0)
                with m.Case():
                    m.d.sync += snake.eq(Mux(snake_up, snake << 1, snake >> 1))
        m.d.comb += Cat(pmod0, pmod1).eq(snake)
        return m


def main(_):
    platform = nexysa7100t.NexysA7100TPlatform()
    platform.add_resources([
        pmod_8ld.Pmod8LDResource(0, conn=('pmod', 0)),
        pmod_8ld.Pmod8LDResource(1, conn=('pmod', 1)),
    ])
    top.build(platform, Demo())

if __name__ == "__main__":
    app.run(main)
