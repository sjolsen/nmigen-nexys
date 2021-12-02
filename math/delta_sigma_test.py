import fractions
import os
import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import util
from nmigen_nexys.math import delta_sigma
from nmigen_nexys.test import test_util


class DeltaSigmaTest(unittest.TestCase):

    def test_sawtooth(self):
        m = Module()
        m.submodules.timer = timer = timer_module.DownTimer(2**12)
        m.submodules.pdm = pdm = delta_sigma.Modulator(5)
        m.d.comb += pdm.input.eq(timer.counter[-5:].as_signed())
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def lowpass():
            yield Passive()
            accum = 0
            i = 0
            while True:
                delta = 1 if (yield pdm.output) else -1
                accum = 0.95 * accum + delta
                print(accum)
                yield

        sim.add_sync_process(lowpass)

        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[timer.counter, pdm.input, pdm.output]):
            sim.run_until(250e-6, run_passive=True)


if __name__ == '__main__':
    unittest.main()
