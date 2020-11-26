"""Tests for nmigen_nexys.board.ulx3s.fm_transmitter."""

import os
import unittest

from nmigen import *
from nmigen.sim import *

from nmigen_nexys.board.ulx3s import fm_transmitter
from nmigen_nexys.core import util
from nmigen_nexys.test import test_util


class TransmitTest(unittest.TestCase):
    """Tests the transmitter against an unclocked pure-simulation receiver."""

    def test_transmit(self):
        m = Module()
        m.submodules.tone = tone = fm_transmitter.ToneGenerator(freq_Hz=440, pcm_depth=16)
        m.submodules.fm = fm = fm_transmitter.FrequencyModulator(carrier_Hz=107_900_000, pcm_depth=tone.pcm_depth)
        m.d.comb += fm.pcm.eq(tone.pcm)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[fm.pcm, fm.output]):
            sim.run_until(1e-3, run_passive=True)


if __name__ == '__main__':
    unittest.main()
