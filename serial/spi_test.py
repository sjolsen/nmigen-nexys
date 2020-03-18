"""Tests for nmigen_nexys.serial.spi."""

from typing import NamedTuple
import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import shift_register
from nmigen_nexys.serial import spi
from nmigen_nexys.test import util


class Example(NamedTuple):
    mosi_data: int
    miso_data: int
    size: int


class ShiftMasterSlaveTest(unittest.TestCase):
    """End-to-end test using example master and slave."""

    def _run_test(self, examples: [Example]):
        m = Module()
        bus = spi.Bus(
            cs_n=Signal(name='cs'),
            clk=Signal(name='clk'),
            mosi=Signal(name='mosi'),
            miso=Signal(name='miso'),
            freq_Hz=1_000_000)
        m.submodules.master = master = spi.ShiftMaster(
            bus, shift_register.Up(16), sim_clk_freq=100_000_000)
        m.submodules.slave = slave = spi.ShiftSlave(
            bus, shift_register.Up(16))
        m.submodules += [master.register, slave.register]
        sim = Simulator(m)
        sim.add_clock(1e-8)  # 100 MHz

        def master_do_one(example: Example):
            yield master.register.word_in.eq(
                example.mosi_data << 16 - example.size)
            yield master.register.latch.eq(1)
            yield master.transfer_size.eq(example.size)
            yield master.start.eq(1)
            yield  # Start
            yield master.register.latch.eq(0)
            yield master.start.eq(0)
            yield from util.WaitDone(master.done)
            actual = yield master.register.word_out[:example.size]
            self.assertEqual(actual, example.miso_data)

        def master_proc():
            for example in examples:
                yield from master_do_one(example)

        def slave_do_one(example: Example):
            yield slave.register.word_in.eq(
                example.miso_data << 16 - example.size)
            yield slave.register.latch.eq(1)
            yield  # Start
            yield slave.register.latch.eq(0)
            yield from util.WaitDone(slave.start)
            yield from util.WaitDone(slave.done)
            overrun = yield slave.overrun
            actual_size = yield slave.transfer_size
            actual = yield slave.register.word_out[:example.size]
            self.assertFalse(overrun)
            self.assertEqual(actual_size, example.size)
            self.assertEqual(actual, example.mosi_data)

        def slave_proc():
            for example in examples:
                yield from slave_do_one(example)

        def timeout():
            yield Passive()
            yield Delay(100e-6)
            self.fail('Timed out after 100 us')

        sim.add_process(timeout)
        sim.add_sync_process(master_proc)
        sim.add_sync_process(slave_proc)
        with util.BazelWriteVCD(sim, "test.vcd", "test.gtkw",
                                traces=list(bus.fields.values())):
            sim.run()

    def test_8(self):
        self._run_test([Example(0xC4, 0x42, 8)])

    def test_12(self):
        self._run_test([Example(0x090, 0x5A5, 12)])

    def test_16(self):
        self._run_test([Example(0xBEEF, 0x1234, 16)])

    def test_multiple(self):
        self._run_test([
            Example(0xC4, 0x42, 8),
            Example(0xBEEF, 0x1234, 16),
            Example(0x090, 0x5A5, 12),
        ])


if __name__ == '__main__':
    unittest.main()
