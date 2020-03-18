"""Tests for nmigen_nexys.board.nexysa7100t.manual_brightness."""

from typing import List
import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.board.nexysa7100t import manual_brightness
from nmigen_nexys.core import util
from nmigen_nexys.display import seven_segment
from nmigen_nexys.test import util as test_util


BLANK = 0
ZERO = seven_segment.DigitLUT.TABLE[0]
ONE = seven_segment.DigitLUT.TABLE[1]
TWO = seven_segment.DigitLUT.TABLE[2]
THREE = seven_segment.DigitLUT.TABLE[3]
FOUR = seven_segment.DigitLUT.TABLE[4]
FIVE = seven_segment.DigitLUT.TABLE[5]
SIX = seven_segment.DigitLUT.TABLE[6]
SEVEN = seven_segment.DigitLUT.TABLE[7]
EIGHT = seven_segment.DigitLUT.TABLE[8]
NINE = seven_segment.DigitLUT.TABLE[9]


class ConversionPipelineTest(unittest.TestCase):

    def test_multiple(self):
        """Test the end-to-end conversion pipeline and output a waveform."""
        m = Module()
        m.submodules.conv = conv = manual_brightness.ConversionPipeline(
            Signal(8), Signal(8))
        rdisp_flat = util.Flatten(m, conv.rdisp)
        ldisp_flat = util.Flatten(m, conv.ldisp)
        sim = Simulator(m)
        sim.add_clock(1e-8)  # 100 MHz

        def convert_one(rval: int, expected_rdisp: List[int],
                        expected_ldisp: List[int]):
            yield conv.rval.eq(rval)
            yield conv.lval.eq(2 * rval)
            yield  # Let conv automatically detect the update
            yield from test_util.WaitDone(conv.done)
            actual_rdisp = []
            yield from test_util.YieldList(conv.rdisp, actual_rdisp)
            actual_ldisp = []
            yield from test_util.YieldList(conv.ldisp, actual_ldisp)
            print(f'Input: {rval}')
            print(f'Expected: {expected_rdisp}, {expected_ldisp}')
            print(f'Actual: {actual_rdisp}, {actual_ldisp}')
            self.assertEqual(expected_rdisp, actual_rdisp)
            self.assertEqual(expected_ldisp, actual_ldisp)

        def convert():
            test_cases = [
                [0, [ZERO, BLANK, BLANK, BLANK], [ZERO, BLANK, BLANK, BLANK]],
                [1, [ONE, BLANK, BLANK, BLANK], [TWO, BLANK, BLANK, BLANK]],
                [2, [TWO, BLANK, BLANK, BLANK], [FOUR, BLANK, BLANK, BLANK]],
                [3, [THREE, BLANK, BLANK, BLANK], [SIX, BLANK, BLANK, BLANK]],
                [10, [ZERO, ONE, BLANK, BLANK], [ZERO, TWO, BLANK, BLANK]],
                [127, [SEVEN, TWO, ONE, BLANK], [FOUR, FIVE, TWO, BLANK]],
            ]
            for rval, rdisp, ldisp in test_cases:
                yield from convert_one(rval, rdisp, ldisp)

        def timeout():
            yield Passive()
            yield Delay(10_000e-8)
            self.fail('Timed out after 10 kcycles')

        sim.add_process(timeout)
        sim.add_sync_process(convert)
        with sim.write_vcd(vcd_file=test_util.BazelTestOutput("test.vcd"),
                           gtkw_file=test_util.BazelTestOutput("test.gtkw"),
                           traces=[conv.rval, rdisp_flat, ldisp_flat]):
            sim.run()


if __name__ == '__main__':
    unittest.main()
