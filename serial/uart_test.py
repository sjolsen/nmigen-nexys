import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import util
from nmigen_nexys.serial import uart
from nmigen_nexys.test import test_util


class TransmitTest(unittest.TestCase):

    def test_transmit(self):
        m = Module()
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        sampling = Signal(name='sampling', reset=0)
        tx_done = Signal()
        rx_done = Signal()
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def transmit():
            yield Passive()
            for _ in range(10):
                yield tx.data.eq(ord('A'))
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield from test_util.WaitSync(tx.done)
            yield tx_done.eq(1)

        def sampling_monitor():
            yield Passive()
            while True:
                # TODO: Use the equivalent of @(posedge|negedge) when it exists.
                yield from test_util.WaitEdge(tx.output)
                self.assertFalse((yield sampling))

        def receive():
            yield Passive()
            for _ in range(10):
                # TODO: Use the equivalent of @negedge when it exists.
                yield from test_util.WaitNegedge(tx.output)
                period = 1 / 12_000_000
                delta = period * 0.25
                yield Delay(period / 2 - delta)
                bits = []
                for i in range(10):
                    yield sampling.eq(1)
                    yield Delay(delta)
                    bits.append((yield tx.output))
                    yield Delay(delta)
                    yield sampling.eq(0)
                    if i != 9:
                        yield Delay(period - 2 * delta)
                # START + 0x41 + STOP
                self.assertEqual(bits, [0] + [1, 0, 0, 0, 0, 0, 1, 0] + [1])
            yield rx_done.eq(1)

        def wait_done():
            yield from test_util.WaitSync(tx_done & rx_done)

        def timeout():
            yield Passive()
            yield Delay(10e-6)
            self.fail('Timed out after 10 us')

        sim.add_sync_process(transmit)
        sim.add_process(sampling_monitor)
        sim.add_process(receive)
        sim.add_sync_process(wait_done)
        sim.add_process(timeout)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[tx.busy, tx.output, sampling]):
            sim.run()


class ReceiveTest(unittest.TestCase):

    def test_transmit(self):
        m = Module()
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.submodules.rx = rx = uart.Receive(12_000_000)
        m.d.comb += rx.input.eq(tx.output)
        tx_done = Signal()
        rx_done = Signal()
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def transmit():
            yield Passive()
            for _ in range(10):
                yield tx.data.eq(ord('A'))
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield from test_util.WaitSync(tx.done)
            yield tx_done.eq(1)

        def receive():
            yield Passive()
            for _ in range(10):
                yield from test_util.WaitSync(rx.start)
                yield from test_util.WaitSync(rx.done)
                self.assertEqual((yield rx.data), ord('A'))
            yield rx_done.eq(1)

        def wait_done():
            yield from test_util.WaitSync(tx_done & rx_done)

        def timeout():
            yield Passive()
            yield Delay(10e-6)
            self.fail('Timed out after 10 us')

        sim.add_sync_process(transmit)
        sim.add_sync_process(receive)
        sim.add_sync_process(wait_done)
        sim.add_process(timeout)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[rx.input, rx.start, rx.done, rx.data]):
            sim.run()


if __name__ == '__main__':
    unittest.main()
