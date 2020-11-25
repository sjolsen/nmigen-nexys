"""Tests for nmigen_nexys.serial.spi."""

import os
from typing import List, NamedTuple
import unittest

from nmigen import *
from nmigen.sim import *

from nmigen_nexys.core import edge
from nmigen_nexys.core import shift_register
from nmigen_nexys.core import util
from nmigen_nexys.serial import spi
from nmigen_nexys.test import test_util


class ClockEngineTest(unittest.TestCase):

    def test_speed(self):
        m = Module()
        bus = spi.Bus(
            cs_n=Signal(name='cs'),
            clk=Signal(name='spi_clk'),
            mosi=Signal(name='mosi'),
            miso=Signal(name='miso'),
            freq_Hz=10_000_000)
        m.submodules.clk_eng = clk_eng = spi.ClockEngine(
            bus, polarity=Signal(reset=0))
        m.submodules.clk_edge = clk_edge = edge.Detector(bus.clk)
        timestamp = Signal(range(100), reset=0)
        m.d.sync += timestamp.eq(timestamp + 1)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def clock_driver():
            yield clk_eng.enable.eq(1)
            yield Delay(1e-6)

        def clock_monitor():
            yield Passive()
            last_edge = None
            while True:
                yield from test_util.WaitSync(clk_edge.rose)
                now = yield timestamp
                if last_edge is not None:
                    self.assertEqual(now - last_edge, 10)
                last_edge = now
                yield

        def timeout():
            yield Passive()
            while True:
                now = yield timestamp
                if now == util.ShapeMax(timestamp):
                    self.fail(f'Timed out after {now} cycles')
                yield

        sim.add_sync_process(clock_driver)
        sim.add_sync_process(clock_monitor)
        sim.add_sync_process(timeout)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=list(bus.fields.values())):
            sim.run()


def MasterDoOne(master: spi.ShiftMaster.Interface, mosi_data: int, size: int):
    """Simulation only: initiate and complete a transaction."""
    yield from master.WriteMosi(C(mosi_data, size))
    yield master.start.eq(1)
    yield  # Start
    yield master.start.eq(0)
    yield from test_util.WaitSync(master.done)
    miso_data = yield master.ReadMiso(size)
    return miso_data


def SlaveDoOne(slave: spi.ShiftSlave, miso_data: int, size: int):
    """Simulation only: await and complete a transaction."""
    yield slave.register.word_in.eq(miso_data << slave.register.width - size)
    yield slave.register.latch.eq(1)
    yield  # Start
    yield slave.register.latch.eq(0)
    yield from test_util.WaitSync(slave.start)
    yield from test_util.WaitSync(slave.done)


class Example(NamedTuple):
    mosi_data: int
    miso_data: int
    size: int


EXAMPLES: List[Example] = [
    Example(0xC4, 0x42, 8),
    Example(0xBEEF, 0x1234, 16),
    Example(0x090, 0x5A5, 12),
]


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
            bus, shift_register.Up(16))
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
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def master_proc():
            yield Passive()
            for example in examples:
                actual = yield from MasterDoOne(
                    master.interface, example.mosi_data, example.size)
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
            yield from test_util.WaitSync(finish)

        def timeout():
            yield Passive()
            yield Delay(100e-6)
            self.fail('Timed out after 100 us')

        sim.add_process(timeout)
        sim.add_sync_process(master_proc)
        sim.add_sync_process(slave_proc)
        sim.add_sync_process(wait_finish)
        test_dir = test_util.BazelTestOutput(self.id())
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

    def test_multiple_mode0(self):
        self._run_test(EXAMPLES, 0, 0)

    def test_multiple_mode1(self):
        self._run_test(EXAMPLES, 0, 1)

    def test_multiple_mode2(self):
        self._run_test(EXAMPLES, 1, 0)

    def test_multiple_mode3(self):
        self._run_test(EXAMPLES, 1, 1)


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
            master_bus, shift_register.Up(16))
        m.submodules.slave = slave = spi.ShiftSlave(
            slave_bus, shift_register.Up(16))
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def master_proc():
            for example in EXAMPLES:
                self.assertNotEqual(example.miso_data, 0)
                actual = yield from MasterDoOne(
                    master.interface, example.mosi_data, example.size)
                self.assertEqual(actual, 0)

        def slave_proc():
            yield Passive()
            for example in EXAMPLES:
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
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        traces = [
            master_bus.cs_n, slave_bus.cs_n, master_bus.clk, master_bus.mosi,
            master_bus.miso,
        ]
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=traces):
            sim.run()


class MultiplexerTest(unittest.TestCase):
    """Test application-side multiplexing."""

    def test_multiplexer(self):
        m = Module()
        bus = spi.Bus(
            cs_n=Signal(name='cs'),
            clk=Signal(name='spi_clk'),
            mosi=Signal(name='mosi'),
            miso=Signal(name='miso'),
            freq_Hz=10_000_000)
        m.submodules.master = master = spi.ShiftMaster(
            bus, shift_register.Up(16))
        m.submodules.slave = slave = spi.ShiftSlave(
            bus, shift_register.Up(16))
        m.submodules.mux = mux = master.Multiplexer(
            len(EXAMPLES), master.interface)
        master_finish = [Signal(reset=0) for _ in range(mux.n)]
        slave_finish = Signal(reset=0)
        finish = Signal()
        m.d.comb += finish.eq(Cat(*master_finish, slave_finish).all())
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def master_proc(n: int):
            def process():
                yield Passive()
                example = EXAMPLES[n]
                yield from test_util.WaitSync(mux.select == n)
                actual = yield from MasterDoOne(
                    mux.interfaces[n], example.mosi_data, example.size)
                self.assertEqual(actual, example.miso_data)
                yield master_finish[n].eq(1)
                yield mux.select.eq(mux.select + 1)
            return process

        def slave_proc():
            yield Passive()
            for example in EXAMPLES:
                yield from SlaveDoOne(slave, example.miso_data, example.size)
                overrun = yield slave.overrun
                actual_size = yield slave.transfer_size
                actual = yield slave.register.word_out[:example.size]
                self.assertFalse(overrun)
                self.assertEqual(actual_size, example.size)
                self.assertEqual(actual, example.mosi_data)
            yield slave_finish.eq(1)

        def wait_finish():
            yield from test_util.WaitSync(finish)

        def timeout():
            yield Passive()
            yield Delay(100e-6)
            self.fail('Timed out after 100 us')

        sim.add_process(timeout)
        for n in range(mux.n):
            sim.add_sync_process(master_proc(n))
        sim.add_sync_process(slave_proc)
        sim.add_sync_process(wait_finish)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=list(bus.fields.values())):
            sim.run()


if __name__ == '__main__':
    unittest.main()
