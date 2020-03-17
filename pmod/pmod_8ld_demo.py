from nmigen import *
from nmigen.build import *

from nexysa7100t import NexysA7100TPlatform
from pmod.pmod_8ld import Pmod8LDResource
from timer import UpTimer


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        clk_period = int(platform.default_clk_frequency)
        m.submodules.timer = timer = UpTimer(clk_period // 10)

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


if __name__ == "__main__":
    platform = NexysA7100TPlatform()
    platform.add_resources([
        Pmod8LDResource(0, conn=('pmod', 0)),
        Pmod8LDResource(1, conn=('pmod', 1)),
    ])
    platform.build(Demo(), do_program=True)
