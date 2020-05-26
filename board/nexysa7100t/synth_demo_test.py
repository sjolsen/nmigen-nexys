import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.board.nexysa7100t import synth_demo
from nmigen_nexys.core import util
from nmigen_nexys.test import test_util


class SynthDemoTest(unittest.TestCase):

    def test_demo(self):
        m = Module()
        m.submodules.demo = demo = synth_demo.SynthDemo()
        m.d.comb += demo.start.eq(1)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[demo.pdm_output]):
            sim.run_until(250e-6, run_passive=True)


if __name__ == '__main__':
    unittest.main()
