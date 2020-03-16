import six

import math
from nmigen import *
from nmigen.back.pysim import *
import unittest

from lut import LinearTransformation, ShapeMin, ShapeMax
from trig import SineLUT


class SineLUTTest(unittest.TestCase):

    def _run_test(self, xshape: Shape, yshape: Shape):
        m = Module()
        m.submodules.sin = sin = SineLUT(Signal(xshape), Signal(yshape))
        sim = Simulator(m)

        if xshape.signed:
            u_x = LinearTransformation(
                imin=ShapeMin(xshape), imax=ShapeMax(xshape) + 1,
                omin=-math.pi, omax=math.pi)
        else:
            u_x = LinearTransformation(
                imin=ShapeMin(xshape), imax=ShapeMax(xshape) + 1,
                omin=0.0, omax=2.0 * math.pi)
        v_y = LinearTransformation(
            imin=ShapeMin(yshape), imax=ShapeMax(yshape) + 1,
            omin=-1.0, omax=1.0)

        y_precision = 2.0 / 2**yshape.width

        def test_one(x: int):
            yield sin.input.eq(x)
            yield Settle()
            y = yield sin.output
            u = u_x(x)
            v = v_y(y)
            expected_v = math.sin(u)
            with self.subTest(x=x):
                try:
                    self.assertAlmostEqual(v, expected_v, delta=y_precision)
                except AssertionError:
                    print(f'x={x} => u={u}')
                    print(f'y={y} => v={v}')
                    print(f'sin(u) = {expected_v}')
                    raise

        def process():
            for x in range(ShapeMin(xshape), ShapeMax(xshape) + 1):
                yield from test_one(x)

        sim.add_process(process)
        sim.run()

    def test_u8(self):
        self._run_test(unsigned(8), unsigned(8))

    def test_i8(self):
        self._run_test(signed(8), signed(8))


if __name__ == '__main__':
    unittest.main()