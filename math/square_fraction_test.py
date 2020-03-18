"""Tests for nmigen_nexys.math.square_fraction."""

import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.math import square_fraction


class SquareFractionTest(unittest.TestCase):
    """Numerically validate a subset of inputs and outputs."""

    def _run_test(self, input: int, expected: int):
        m = Module()
        m.submodules.sf = sf = square_fraction.SquareFraction(Signal(8))
        sim = Simulator(m)

        def process():
            yield sf.input.eq(input)
            yield Settle()
            actual = yield sf.output
            for port in sf.ports:
                signal = getattr(sf, port)
                value = yield signal
                print(f'{port}: 0b{value:0{signal.width}b}')
            self.assertEqual(expected, actual)

        sim.add_process(process)
        sim.run()

    def test_zero(self):
        self._run_test(input=0b0000_0000, expected=0b0000_0000)

    def test_0b1000_1000(self):
        self._run_test(input=0b1000_1000, expected=0b0100_1000)

    def test_max(self):
        self._run_test(input=0b1111_1111, expected=0b1111_1110)


if __name__ == '__main__':
    unittest.main()
