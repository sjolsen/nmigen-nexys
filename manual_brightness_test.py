import six

from nmigen import *
from nmigen.back.pysim import *
import os
from typing import List
import unittest

from bcd import DigitLUT
from manual_brightness import ConversionPipeline


BLANK = 0
ZERO = DigitLUT.TABLE[0]
ONE = DigitLUT.TABLE[1]
TWO = DigitLUT.TABLE[2]
THREE = DigitLUT.TABLE[3]
FOUR = DigitLUT.TABLE[4]
FIVE = DigitLUT.TABLE[5]
SIX = DigitLUT.TABLE[6]
SEVEN = DigitLUT.TABLE[7]
EIGHT = DigitLUT.TABLE[8]
NINE = DigitLUT.TABLE[9]


def YieldList(l, result):
    for x in l:
        y = yield x
        result.append(y)


def WaitDone(done):
    while True:
        x = yield done
        if x:
            break
        yield


def Flatten(m: Module, input: List[Signal]) -> Signal:
    cat = Cat(*input)
    flat = Signal(cat.shape())
    m.d.comb += flat.eq(cat)
    return flat


class ConversionPipelineTest(unittest.TestCase):

    def test_multiple(self):
        m = Module()
        m.submodules.conv = conv = ConversionPipeline(Signal(8), Signal(8))
        rdisp_flat = Flatten(m, conv.rdisp)
        ldisp_flat = Flatten(m, conv.ldisp)
        sim = Simulator(m)
        sim.add_clock(1e-8)  # 100 MHz

        def convert_one(rval: int, expected_rdisp: List[int], expected_ldisp: List[int]):
            yield conv.rval.eq(rval)
            yield conv.lval.eq(2 * rval)
            yield  # Let conv automatically detect the update
            yield from WaitDone(conv.done)
            actual_rdisp = []
            yield from YieldList(conv.rdisp, actual_rdisp)
            actual_ldisp = []
            yield from YieldList(conv.ldisp, actual_ldisp)
            print(f'Input: {rval}')
            print(f'Expected: {expected_rdisp}, {expected_ldisp}')
            print(f'Actual: {actual_rdisp}, {actual_ldisp}')
            self.assertEqual(expected_rdisp, actual_rdisp)
            self.assertEqual(expected_ldisp, actual_ldisp)

        def convert():
            TEST_CASES = [
                [0, [ZERO, BLANK, BLANK, BLANK], [ZERO, BLANK, BLANK, BLANK]],
                [1, [ONE, BLANK, BLANK, BLANK], [TWO, BLANK, BLANK, BLANK]],
                [2, [TWO, BLANK, BLANK, BLANK], [FOUR, BLANK, BLANK, BLANK]],
                [3, [THREE, BLANK, BLANK, BLANK], [SIX, BLANK, BLANK, BLANK]],
                [10, [ZERO, ONE, BLANK, BLANK], [ZERO, TWO, BLANK, BLANK]],
                [127, [SEVEN, TWO, ONE, BLANK], [FOUR, FIVE, TWO, BLANK]],
            ]
            for rval, rdisp, ldisp in TEST_CASES:
                yield from convert_one(rval, rdisp, ldisp)

        def timeout():
            yield Passive()
            yield Delay(10_000e-8)
            self.fail('Timed out after 10 kcycles')

        def outfile(basename):
            outdir = os.getenv('TEST_UNDECLARED_OUTPUTS_DIR')
            if outdir is None:
                return basename
            else:
                return os.path.join(outdir, basename)

        sim.add_process(timeout)
        sim.add_sync_process(convert)
        with sim.write_vcd(
            vcd_file=outfile("test.vcd"),
            gtkw_file=outfile("test.gtkw"),
            traces=[conv.rval, rdisp_flat, ldisp_flat]):
            sim.run()


if __name__ == '__main__':
    unittest.main()