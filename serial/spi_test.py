"""Tests for nmigen_nexys.serial.spi."""

from typing import NamedTuple
import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import shift_register
from nmigen_nexys.serial import spi
from nmigen_nexys.test import util


def MasterDoOne(master: spi.ShiftMaster, mosi_data: int, size: int):
    """Simulation only: initiate and complete a transaction."""
    yield master.register.word_in.eq(mosi_data << master.register.width - size)
    yield master.register.latch.eq(1)
    yield master.transfer_size.eq(size)
    yield master.start.eq(1)
    yield  # Start
    yield master.register.latch.eq(0)
    yield master.start.eq(0)
    yield from util.WaitDone(master.done)


def SlaveDoOne(slave: spi.ShiftSlave, miso_data: int, size: int):
    """Simulation only: await and complete a transaction."""
    yield slave.register.word_in.eq(miso_data << slave.register.width - size)
    yield slave.register.latch.eq(1)
    yield  # Start
    yield slave.register.latch.eq(0)
    yield from util.WaitDone(slave.start)
    yield from util.WaitDone(slave.done)


class Example(NamedTuple):
    mosi_data: int
    miso_data: int
    size: int


class ShiftMasterSlaveTest(unittest.TestCase):
    """End-to-end test using example master and slave."""

    def _run_test(self, examples: [Example], polarity: int = 0, phase: int = 0):
        m = Module()
        bus = spi.Bus(
            cs_n=Signal(name='cs'),
            clk=Signal(name='spi_clk'),
            mosi=Signal(name='mosi'),
            miso=Signal(name='miso'),
            freq_Hz=10_000_000)
        m.submodules.master = master = spi.ShiftMaster(
            bus, shift_register.Up(16), sim_clk_freq=100_000_000)
        m.submodules.slave = slave = spi.ShiftSlave(
            bus, shift_register.Up(16))
        m.d.comb += master.polarity.eq(polarity)
        m.d.comb += master.phase.eq(phase)
        m.d.comb += slave.polarity.eq(polarity)
        m.d.comb += slave.phase.eq(phase)
        master_finish = Signal(reset=0)
        slave_finish = Signal(reset=0)
        finish = Signal()
        m.d.comb += finish.eq(master_finish & slave_finish)
        sim = Simulator(m)
        sim.add_clock(1e-8)  # 100 MHz

        def master_proc():
            yield Passive()
            for example in examples:
                yield from MasterDoOne(master, example.mosi_data, example.size)
                actual = yield master.register.word_out[:example.size]
                self.assertEqual(actual, example.miso_data)
            yield master_finish.eq(1)

        def slave_proc():
            yield Passive()
            for example in examples:
                yield from SlaveDoOne(slave, example.miso_data, example.size)
                overrun = yield slave.overrun
                actual_size = yield slave.transfer_size
                actual = yield slave.register.word_out[:example.size]
                self.assertFalse(overrun)
                self.assertEqual(actual_size, example.size)
                self.assertEqual(actual, example.mosi_data)
            yield slave_finish.eq(1)

        def wait_finish():
            yield from util.WaitDone(finish)

        def timeout():
            yield Passive()
            yield Delay(100e-6)
            self.fail('Timed out after 100 us')

        sim.add_process(timeout)
        sim.add_sync_process(master_proc)
        sim.add_sync_process(slave_proc)
        sim.add_sync_process(wait_finish)
        test_dir = util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=list(bus.fields.values())):
            sim.run()

    def test_8(self):
        self._run_test([Example(0xC4, 0x42, 8)])

    def test_12(self):
        self._run_test([Example(0x090, 0x5A5, 12)])

    def test_16(self):
        self._run_test([Example(0xBEEF, 0x1234, 16)])

    EXAMPLES = [
        Example(0xC4, 0x42, 8),
        Example(0xBEEF, 0x1234, 16),
        Example(0x090, 0x5A5, 12),
    ]

    def test_multiple_mode0(self):
        self._run_test(self.EXAMPLES, 0, 0)

    def test_multiple_mode1(self):
        self._run_test(self.EXAMPLES, 0, 1)

    def test_multiple_mode2(self):
        self._run_test(self.EXAMPLES, 1, 0)

    def test_multiple_mode3(self):
        self._run_test(self.EXAMPLES, 1, 1)


class NoChipSelectTest(unittest.TestCase):
    """Validates slave behavior when chip select is deasserted."""

    def test_no_slave_activity(self):
        m = Module()
        master_bus = spi.Bus(
            cs_n=Signal(name='master_cs'),
            clk=Signal(name='spi_clk'),
            mosi=Signal(name='mosi'),
            miso=Signal(name='miso'),
            freq_Hz=10_000_000)
        slave_bus = spi.Bus(
            cs_n=Signal(name='slave_cs', reset=1),
            clk=master_bus.clk,
            mosi=master_bus.mosi,
            miso=master_bus.miso,
            freq_Hz=10_000_000)
        m.submodules.master = master = spi.ShiftMaster(
            master_bus, shift_register.Up(16), sim_clk_freq=100_000_000)
        m.submodules.slave = slave = spi.ShiftSlave(
            slave_bus, shift_register.Up(16))
        sim = Simulator(m)
        sim.add_clock(1e-8)  # 100 MHz

        def master_proc():
            for example in ShiftMasterSlaveTest.EXAMPLES:
                self.assertNotEqual(example.miso_data, 0)
                yield from MasterDoOne(master, example.mosi_data, example.size)
                actual = yield master.register.word_out[:example.size]
                self.assertEqual(actual, 0)

        def slave_proc():
            yield Passive()
            for example in ShiftMasterSlaveTest.EXAMPLES:
                yield from SlaveDoOne(slave, example.miso_data, example.size)
                self.fail('Slave transfer should not have completed!')

        def always_monitor(signal: Signal, expected: int):
            def monitor():
                yield Passive()
                while True:
                    actual = yield signal
                    if actual != expected:
                        self.fail(
                            f'Signal {signal.name}: {actual} != {expected}')
                    yield
            return monitor

        def timeout():
            yield Passive()
            yield Delay(100e-6)
            self.fail('Timed out after 100 us')

        sim.add_process(timeout)
        sim.add_sync_process(master_proc)
        sim.add_sync_process(slave_proc)
        sim.add_sync_process(always_monitor(slave.start, 0))
        sim.add_sync_process(always_monitor(slave.done, 0))
        sim.add_sync_process(always_monitor(slave.register.shift, 0))
        sim.add_sync_process(always_monitor(master_bus.miso, 0))
        test_dir = util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        traces = [
            master_bus.cs_n, slave_bus.cs_n, master_bus.clk, master_bus.mosi,
            master_bus.miso,
        ]
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=traces):
            sim.run()


if __name__ == '__main__':
    unittest.main()
