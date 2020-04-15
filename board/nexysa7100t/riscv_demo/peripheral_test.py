from typing import List
import unittest

from minerva import core
from nmigen import *
from nmigen.back.pysim import *
from nmigen.hdl.rec import Record

from nmigen_nexys.board.nexysa7100t.riscv_demo import peripheral
from nmigen_nexys.core import util
from nmigen_nexys.test import test_util


class PeripheralTest(unittest.TestCase):

    def _wishbone_traces(self, wbus: Record) -> List[Signal]:
        return [
            wbus.cyc,
            wbus.stb,
            wbus.adr,
            wbus.sel,
            wbus.we,
            wbus.dat_w,
            wbus.dat_r,
            wbus.ack,
            wbus.err,
        ]

    def test_activity(self):
        m = Module()
        m.submodules.cpu = cpu = core.Minerva(with_debug=True)
        m.submodules.periph = periph = peripheral.Peripherals()
        m.d.comb += cpu.ibus.connect(periph.ibus)
        m.d.comb += cpu.dbus.connect(periph.dbus)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        traces = sum([
            self._wishbone_traces(periph.ibus),
            self._wishbone_traces(periph.dbus),
        ], [])
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=traces):
            sim.run_until(10e-6, run_passive=True)


if __name__ == '__main__':
    unittest.main()
