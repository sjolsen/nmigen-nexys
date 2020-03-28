"""Tests for nmigen_nexys.board.nexysa7100t.uart_demo."""

import unittest

from nmigen import *
from nmigen.back.pysim import *
from nmigen.hdl.rec import *

from nmigen_nexys.board.nexysa7100t import uart_demo
from nmigen_nexys.core import util
from nmigen_nexys.serial import uart
from nmigen_nexys.test import test_util


class UARTDemoTest(unittest.TestCase):
    """Test the response data for several possible inputs."""

    def _run_test(self, c: str, expected: bytes, runs: int = 1):
        m = Module()
        pins = Record(Layout([
            ('rx', 1, Direction.FANIN),
            ('tx', 1, Direction.FANOUT),
            ('rts', 1, Direction.FANOUT),
            ('cts', 1, Direction.FANIN),
        ]))
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.submodules.rx = rx = uart.Receive(12_000_000)
        m.submodules.demo = uart_demo.UARTDemo(pins)
        m.d.comb += pins.rx.eq(tx.output)
        m.d.comb += rx.input.eq(pins.tx)
        tx_done = Signal(range(runs + 1))
        rx_done = Signal(range(runs + 1))
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def transmit():
            yield Passive()
            for i in range(runs):
                yield from test_util.WaitSync(rx_done >= i)
                yield tx.data.eq(ord(c))
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield from test_util.WaitSync(tx.done)
                yield tx_done.eq(tx_done + 1)

        def receive():
            yield Passive()
            for _ in range(runs):
                data = bytearray()
                for _ in range(len(expected)):
                    yield from test_util.WaitSync(rx.start)
                    yield from test_util.WaitSync(rx.done)
                    data.append((yield rx.data))
                self.assertEqual(data, expected)
                yield rx_done.eq(rx_done + 1)

        def wait_done():
            yield from test_util.WaitSync((tx_done == runs) & (rx_done == runs))

        def timeout():
            yield Passive()
            us = 12 * runs
            yield Delay(us * 1e-6)
            self.fail(f'Timed out after {us} us')

        sim.add_sync_process(transmit)
        sim.add_sync_process(receive)
        sim.add_sync_process(wait_done)
        sim.add_process(timeout)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[tx.output, rx.input]):
            sim.run()

    def test_nul(self):
        self._run_test('\0', b"'\0' = 0x00\r\n")

    def test_tab(self):
        self._run_test('\t', b"'\t' = 0x09\r\n")

    def test_A(self):
        self._run_test('A', b"'A' = 0x41\r\n")

    def test_a(self):
        self._run_test('a', b"'a' = 0x61\r\n")


if __name__ == '__main__':
    unittest.main()
