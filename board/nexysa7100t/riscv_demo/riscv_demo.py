from absl import app
from minerva import core
from nmigen import *
from nmigen.build import *
from rules_python.python.runfiles import runfiles

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.board.nexysa7100t.riscv_demo import peripheral
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
            # TODO: RTS and CTS should probably be swapped in RemoteBitbang
            uart.cts.eq(rbb.uart.rts_n),
            rbb.uart.cts_n.eq(uart.rts),
        ]
        m.d.comb += [
            cpu.jtag.tck.eq(rbb.jtag.tck),
            cpu.jtag.tdi.eq(rbb.jtag.tdi),
            rbb.jtag.tdo.eq(cpu.jtag.tdo),
            cpu.jtag.tms.eq(rbb.jtag.tms),
            cpu.jtag.trst.eq(rbb.jtag.trst),
        ]
        # Connect peripherals to the CPU and external world
        r = runfiles.Create()
        m.submodules.periph = periph = peripheral.Peripherals(r.Rlocation(
            'nmigen_nexys/board/nexysa7100t/riscv_demo/main.bin'))
        m.d.comb += platform.request('display_7seg').eq(periph.segments)
        m.d.comb += platform.request('display_7seg_an').eq(periph.anodes)
        m.d.comb += cpu.ibus.connect(periph.ibus)
        m.d.comb += cpu.dbus.connect(periph.dbus)
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), RiscvDemo())

if __name__ == "__main__":
    app.run(main)
