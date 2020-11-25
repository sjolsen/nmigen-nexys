import os
from typing import List, NamedTuple
import unittest

from minerva import core
from nmigen import *
from nmigen.sim import *
from nmigen.hdl.rec import Record
from rules_python.python.runfiles import runfiles

from nmigen_nexys.board.nexysa7100t.riscv_demo import peripheral
from nmigen_nexys.core import util
from nmigen_nexys.test import event
from nmigen_nexys.test import test_util


class Read(NamedTuple):
    adr: int


class ReadAck(NamedTuple):
    dat_r: int


class Write(NamedTuple):
    adr: int
    sel: int
    dat_w: int


class WriteAck(NamedTuple):
    pass


class Error(NamedTuple):
    pass


class WishboneMonitor(event.Monitor):

    def __init__(self, wbus: Record):
        super().__init__()
        self.wbus = wbus

    def process(self) -> test_util.CoroutineProcess[None]:
        yield Passive()
        while True:
            if (yield self.wbus.cyc):
                stb = yield self.wbus.stb
                adr = yield self.wbus.adr
                we = yield self.wbus.we
                ack = yield self.wbus.ack
                if stb and not we:
                    yield from self.emit(Read(adr=adr))
                if stb and we:
                    yield from self.emit(Write(
                        adr=adr,
                        sel=(yield self.wbus.sel),
                        dat_w=(yield self.wbus.dat_w)))
                if ack and not we:
                    yield from self.emit(ReadAck(dat_r=(yield self.wbus.dat_r)))
                if ack and we:
                    yield from self.emit(WriteAck())
                if (yield self.wbus.err):
                    yield from self.emit(Error())
            yield


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
        r = runfiles.Create()
        m.submodules.cpu = cpu = core.Minerva(with_debug=True)
        m.submodules.periph = periph = peripheral.Peripherals(r.Rlocation(
            'nmigen_nexys/board/nexysa7100t/riscv_demo/deadbeef.bin'))
        m.d.comb += cpu.ibus.connect(periph.ibus)
        m.d.comb += cpu.dbus.connect(periph.dbus)
        # TODO: enable timeout
        m.submodules.timer = timer = test_util.Timer(self, timeout_s=1e-6)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        events = event.EventSeries(timer.cycle_counter)
        wmon = WishboneMonitor(periph.dbus)
        wmon.attach(sim, events)

        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        traces = sum([
            self._wishbone_traces(periph.ibus),
            self._wishbone_traces(periph.dbus),
        ], [])
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=traces):
            sim.run_until(1e-6, run_passive=True)

        events.ShowEvents()
        events.ValidateConstraints(self, [
            Write(adr=0x2000 >> 2, sel=0b1111, dat_w=0xdeadbeef),
            WriteAck(),
        ])


if __name__ == '__main__':
    unittest.main()
