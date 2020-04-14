from absl import app
from minerva import core
from nmigen import *
from nmigen.build import *

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.board.nexysa7100t.riscv_demo import memory
from nmigen_nexys.debug import remote_bitbang


class RiscvDemo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        m.submodules.cpu = cpu = core.Minerva(with_debug=True)
        # Linux tools don't like it when I try to use 12 Mbaud :(
        m.submodules.rbb = rbb = remote_bitbang.RemoteBitbang(3_000_000)
        uart = platform.request('uart', 0)
        m.d.comb += [
            rbb.uart.rx.eq(uart.rx),
            uart.tx.eq(rbb.uart.tx),
            uart.rts.eq(rbb.uart.rts_n),
            rbb.uart.cts_n.eq(uart.cts),
        ]
        m.d.comb += [
            cpu.jtag.tck.eq(rbb.jtag.tck),
            cpu.jtag.tdi.eq(rbb.jtag.tdi),
            rbb.jtag.tdo.eq(cpu.jtag.tdo),
            cpu.jtag.tms.eq(rbb.jtag.tms),
            cpu.jtag.trst.eq(rbb.jtag.trst),
        ]
        # Set up RAM
        m.submodules.ram = ram = memory.RAM()
        m.d.comb += cpu.ibus.connect(ram.ibus)
        m.d.comb += cpu.dbus.connect(ram.dbus)
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), RiscvDemo())

if __name__ == "__main__":
    app.run(main)
