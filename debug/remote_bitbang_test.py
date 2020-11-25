import contextlib
import os
from typing import NamedTuple
import unittest

from nmigen import *
from nmigen.hdl.ast import SignalSet
from nmigen.sim import *

from nmigen_nexys.core import edge
from nmigen_nexys.core import util
from nmigen_nexys.debug import remote_bitbang
from nmigen_nexys.serial import uart
from nmigen_nexys.test import event
from nmigen_nexys.test import test_util


class RemoteBitbagTest(unittest.TestCase):

    def _traces(self, rbb: remote_bitbang.RemoteBitbang):
        return [
            *rbb.uart.fields.values(),
            *rbb.jtag.fields.values(),
            rbb.blink,
        ]

    def test_no_overrun(self, runs: int = 30):
        m = Module()
        m.submodules.rbb = rbb = remote_bitbang.RemoteBitbang(12_000_000)
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.submodules.rx = rx = uart.Receive(12_000_000)
        m.d.comb += rbb.uart.rx.eq(tx.output)
        m.d.comb += rbb.uart.cts_n.eq(0)
        m.d.comb += rx.input.eq(rbb.uart.tx)
        m.submodules.timer = timer = test_util.Timer(self, timeout_s=runs * 1e-6)
        tx_done = Signal()
        rx_done = Signal()
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def transmit():
            yield Passive()
            for i in range(runs):
                yield tx.data.eq(ord('R'))
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield
                # Wait a tick for the RBB server to latch the old value
                yield rbb.jtag.tdo.eq(i & 1)
                yield from test_util.WaitSync(tx.done)
            yield tx_done.eq(1)

        def receive():
            yield Passive()
            expected = [ord('0') | (i & 1) for i in range(runs)]
            actual = []
            for _ in range(runs):
                yield from test_util.WaitSync(rx.start)
                yield from test_util.WaitSync(rx.done)
                actual.append((yield rx.data))
            self.assertSequenceEqual(actual, expected)
            yield rx_done.eq(1)

        def monitor():
            yield Active()
            yield from test_util.WaitSync(tx_done & rx_done)

        sim.add_sync_process(transmit)
        sim.add_sync_process(receive)
        sim.add_sync_process(monitor)
        sim.add_sync_process(timer.timeout_process)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=self._traces(rbb)):
            sim.run()

    class _EdgeTestContext(NamedTuple):
        rbb: remote_bitbang.RemoteBitbang
        tx: uart.Transmit
        timer: test_util.Timer
        constraints: event.EventConstraints

    @contextlib.contextmanager
    def _run_edge_test(self, tx_data: str):
        m = Module()
        m.submodules.rbb = rbb = remote_bitbang.RemoteBitbang(12_000_000)
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.d.comb += rbb.uart.rx.eq(tx.output)
        m.d.comb += rbb.uart.cts_n.eq(0)
        m.submodules.timer = timer = test_util.Timer(
            self, timeout_s=len(tx_data) * 1e-6)
        # Auto-generate edge detectors based on the concrete test configuration
        constraints = []
        yield self._EdgeTestContext(rbb, tx, timer, constraints)
        signals_to_monitor = SignalSet(
            ev.signal for ev in constraints if isinstance(ev, event.EdgeEvent))
        # Always monitor JTAG signals + blink
        signals_to_monitor |= SignalSet(rbb.jtag.fields.values())
        signals_to_monitor |= SignalSet([rbb.blink])
        detectors = [edge.Detector(sig) for sig in signals_to_monitor]
        for detector in detectors:
            m.submodules[detector.input.name] = detector
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        events = event.EventSeries(timer.cycle_counter)
        edge_monitor = event.EdgeMonitor(detectors)

        def transmit():
            yield Active()
            for c in tx_data:
                yield tx.data.eq(ord(c))
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield from test_util.WaitSync(tx.done)
            # Yield a couple more times to pick up edges
            yield
            yield

        sim.add_sync_process(transmit)
        edge_monitor.attach(sim, events)
        sim.add_sync_process(timer.timeout_process)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=self._traces(rbb)):
            sim.run()

        events.ShowEvents()
        events.ValidateConstraints(self, constraints)

    def test_edges_blink(self):
        with self._run_edge_test('Bb') as ctx:
            ctx.constraints.extend([
                event.EdgeEvent(ctx.rbb.blink, 'rose'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.blink, 'fell'),
            ])

    def test_edges_read(self):
        with self._run_edge_test('R') as ctx:
            ctx.constraints.extend([])

    def test_edges_quit(self):
        with self._run_edge_test('Q') as ctx:
            ctx.constraints.extend([])

    def test_edges_write_serial(self):
        # Running through with a Gray code avoids having to handle simultaneous
        # events :)
        with self._run_edge_test('13267540') as ctx:
            ctx.constraints.extend([
                event.EdgeEvent(ctx.rbb.jtag.tdi, 'rose'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.tms, 'rose'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.tdi, 'fell'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.tck, 'rose'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.tdi, 'rose'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.tms, 'fell'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.tdi, 'fell'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.tck, 'fell'),
            ])

    def test_edges_write_reset(self):
        # Running through with a Gray code avoids having to handle simultaneous
        # events :)
        with self._run_edge_test('sutr') as ctx:
            ctx.constraints.extend([
                event.EdgeEvent(ctx.rbb.jtag.srst, 'rose'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.trst, 'rose'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.srst, 'fell'),
                event.MinDelay(seconds=9 / 12_000_000),
                event.EdgeEvent(ctx.rbb.jtag.trst, 'fell'),
            ])


if __name__ == '__main__':
    unittest.main()
