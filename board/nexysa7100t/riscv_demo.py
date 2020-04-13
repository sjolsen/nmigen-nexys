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
        m.submodules.cpu = cpu = core.Minerva(with_debug=True)
        m.submodules.bscan = bscan = primitive.BscanE2()
        m.d.comb += [
            cpu.jtag.tck.eq(bscan.tck),
            cpu.jtag.tdi.eq(bscan.tdi),
            bscan.tdo.eq(cpu.jtag.tdo),
            cpu.jtag.tms.eq(bscan.tms),
            cpu.jtag.trst.eq(bscan.reset),
        ]
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), RiscvDemo())

if __name__ == "__main__":
    app.run(main)
