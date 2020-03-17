import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.math import bcd
from nmigen_nexys.test import util


class BinToBCDTest(unittest.TestCase):

    def _run_test(self, input: int, expected: [int]):
        m = Module()
        m.submodules.b2d = b2d = bcd.BinToBCD(
            input=Signal(range(input + 1)),
            output=[Signal(4) for _ in expected])
        sim = Simulator(m)
        sim.add_clock(1e-8)  # 100 MHz

        def convert():
            yield b2d.input.eq(input)
            yield b2d.start.eq(1)
            yield  # Update input and start
            yield from util.WaitDone(b2d.done)
            actual = []
            yield from util.YieldList(b2d.output, actual)
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
        self._run_test(input=0, expected=[0])
        self._run_test(input=0, expected=[0, 0])
        self._run_test(input=0, expected=[0, 0, 0])
        self._run_test(input=0, expected=[0, 0, 0, 0])

    def test_256(self):
        self._run_test(input=256, expected=[6, 5, 2])
        self._run_test(input=256, expected=[6, 5, 2, 0])

    def test_1024(self):
        self._run_test(input=1024, expected=[4, 2, 0, 1])

    def test_max(self):
        self._run_test(input=9999, expected=[9, 9, 9, 9])


if __name__ == '__main__':
    unittest.main()
