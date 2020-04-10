from absl import app
from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import top
from nmigen_nexys.vendor.xilinx import macro


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        sw_a = [platform.request('switch', i) for i in range(0, 8)]
        sw_b = [platform.request('switch', i) for i in range(8, 16)]
        leds = [platform.request('led', i) for i in range(9)]
        m.submodules.adder = adder = macro.AddSub(width=8)
        m.d.comb += adder.a.eq(Cat(*sw_a))
        m.d.comb += adder.b.eq(Cat(*sw_b))
        m.d.comb += adder.add_sub.eq(adder.op.ADD)
        m.d.comb += adder.ce.eq(1)
        m.d.comb += Cat(*leds).eq(Cat(adder.result, adder.carryout))
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), Demo())

if __name__ == "__main__":
    app.run(main)
