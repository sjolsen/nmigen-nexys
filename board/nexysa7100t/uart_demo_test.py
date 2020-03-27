import unittest

from nmigen import *
from nmigen.back.pysim import *
from nmigen.hdl.rec import *

from nmigen_nexys.board.nexysa7100t import uart_demo
from nmigen_nexys.core import util
from nmigen_nexys.serial import uart
from nmigen_nexys.test import test_util


class UARTDemoTest(unittest.TestCase):

    def _run_test(self, c: str, expected: bytes):
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
        tx_done = Signal()
        rx_done = Signal()
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def transmit():
            yield Passive()
            yield tx.data.eq(ord(c))
            yield tx.start.eq(1)
            yield
            yield tx.start.eq(0)
            yield from test_util.WaitSync(tx.done)
            yield tx_done.eq(1)

        def receive():
            yield Passive()
            data = bytearray()
            for _ in range(len(expected)):
                yield from test_util.WaitSync(rx.start)
                yield from test_util.WaitSync(rx.done)
                data.append((yield rx.data))
            self.assertEqual(data, expected)
            yield rx_done.eq(1)

        def wait_done():
            yield from test_util.WaitSync(tx_done & rx_done)

        def timeout():
            yield Passive()
            yield Delay(15e-6)
            self.fail('Timed out after 15 us')

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
        self._run_test('\0', b"'\0' =  0\r\n")

    def test_tab(self):
        self._run_test('\t', b"'\t' =  9\r\n")

    def test_A(self):
        self._run_test('A', b"'A' = 65\r\n")

    def test_a(self):
        self._run_test('a', b"'a' = 97\r\n")


if __name__ == '__main__':
    unittest.main()
