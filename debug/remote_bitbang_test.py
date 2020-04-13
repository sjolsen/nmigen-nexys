import os
import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import util
from nmigen_nexys.debug import remote_bitbang
from nmigen_nexys.serial import uart
from nmigen_nexys.test import test_util


class RemoteBitbagTest(unittest.TestCase):
    """Simulate and validate the power-sequencing logic."""

    TIMEOUT_S = 50e-6

    def test_some_commands(self):
        m = Module()
        m.submodules.rbb = rbb = remote_bitbang.RemoteBitbang()
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.d.comb += rbb.uart.rx.eq(tx.output)
        m.d.comb += rbb.uart.cts.eq(1)
        m.submodules.timer = timer = test_util.Timer(self, self.TIMEOUT_S)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def client():
            cmds = 'BbRQ01234567rstu'
            for cmd in cmds:
                yield tx.data.eq(ord(cmd))
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield from test_util.WaitSync(tx.done)

        sim.add_sync_process(client)
        sim.add_sync_process(timer.timeout_process)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        traces = [
            *rbb.uart.fields.values(),
            *rbb.jtag.fields.values(),
            rbb.blink,
        ]
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=traces):
            sim.run()


if __name__ == '__main__':
    unittest.main()
