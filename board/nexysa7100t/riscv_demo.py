from absl import app
from minerva import core
from nmigen import *
from nmigen.build import *

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.vendor.xilinx import primitive


class RiscvDemo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # m.submodules.cpu = cpu = core.Minerva(with_debug=True)
        # m.submodules.bscan = bscan = primitive.BscanE2()
        jtag = platform.request('jtag', 0)
        # m.d.comb += [
        #     cpu.jtag.tck.eq(jtag.tck),
        #     cpu.jtag.tdi.eq(jtag.tdi),
        #     jtag.tdo.eq(cpu.jtag.tdo),
        #     cpu.jtag.tms.eq(jtag.tms),
        #     # cpu.jtag.trst.eq(reset),
        # ]
        leds = [platform.request('led', i) for i in range(4)]
        m.d.comb += Cat(*leds).eq(jtag)
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), RiscvDemo())

if __name__ == "__main__":
    app.run(main)
