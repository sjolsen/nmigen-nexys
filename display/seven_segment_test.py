"""Tests for nmigen_nexys.display.seven_segment."""

import unittest

from nmigen import *
from nmigen.sim import *

from nmigen_nexys.core import util
from nmigen_nexys.display import seven_segment
from nmigen_nexys.test import test_util


BLANK = 0
ZERO = 0b00111111
ONE = 0b00000110
TWO = 0b01011011
FOUR = 0b01100110
FIVE = 0b01101101
SIX = 0b01111101
NINE = 0b01101111


class BCDRendererTest(unittest.TestCase):
    """Test the rendering of multi-digit BCD values."""

    def _run_test(self, input: [int], expected: [int]):
        m = Module()
        m.submodules.bcdr = bcdr = seven_segment.BCDRenderer(
            [Signal(4) for _ in input])
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def convert():
            for sig, val in zip(bcdr.input, input):
                yield sig.eq(val)
            yield bcdr.start.eq(1)
            yield  # Update input and start
            yield from test_util.WaitSync(bcdr.done)
            actual = yield from test_util.YieldList(bcdr.output)
            print(f'Input: {input}')
            print(f'Expected: {expected}')
            print(f'Actual: {actual}')
            self.assertEqual(expected, actual)

        def timeout():
            yield Passive()
            yield Delay(10e-8)
            self.fail('Timed out after 10 cycles')

        sim.add_process(timeout)
        sim.add_sync_process(convert)
        sim.run()

    def test_zero(self):
        """0 should render as "   0", not "0000" or "    "."""
        self._run_test(
            input=[0, 0, 0, 0], expected=[ZERO, BLANK, BLANK, BLANK])

    def test_256(self):
        """256 should render as " 256", not "0256"."""
        self._run_test(input=[6, 5, 2, 0], expected=[SIX, FIVE, TWO, BLANK])

    def test_1024(self):
        self._run_test(input=[4, 2, 0, 1], expected=[FOUR, TWO, ZERO, ONE])

    def test_max(self):
        self._run_test(input=[9, 9, 9, 9], expected=[NINE, NINE, NINE, NINE])


if __name__ == '__main__':
    unittest.main()
