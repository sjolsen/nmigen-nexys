"""Simulation waveform generator for nmigen_nexys.display.seven_segment."""

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import util
from nmigen_nexys.display import seven_segment
from nmigen_nexys.test import test_util


if __name__ == "__main__":
    m = Module()
    segments = Signal(8)
    anodes = Signal(8)
    m.submodules.demo = seven_segment.DisplayMultiplexerDemo(segments, anodes)
    sim = Simulator(m)
    sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)
    with sim.write_vcd(test_util.BazelTestOutput("test.vcd"),
                       test_util.BazelTestOutput("test.gtkw"),
                       traces=[segments, anodes]):
        sim.run_until(100e-6, run_passive=True)
