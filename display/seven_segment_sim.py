"""Simulation waveform generator for nmigen_nexys.display.seven_segment."""

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.display import seven_segment
from nmigen_nexys.test import util


if __name__ == "__main__":
    m = Module()
    segments = Signal(8)
    anodes = Signal(8)
    m.submodules.demo = seven_segment.DisplayMultiplexerDemo(segments, anodes)
    sim = Simulator(m)
    sim.add_clock(1e-8)
    with util.BazelWriteVCD(
            sim, "test.vcd", "test.gtkw", traces=[segments, anodes]):
        sim.run_until(100e-6, run_passive=True)
