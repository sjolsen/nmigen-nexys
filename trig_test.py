import six

import abc
import math
from nmigen import *
from nmigen.back.pysim import *
from typing import Callable
import unittest

from lut import LinearTransformation, ShapeMin, ShapeMax
from trig import CosineLUT, SineLUT


class SinusoidTestBase(abc.ABC):

    @abc.abstractproperty
    def real_fun(self) -> Callable[[float], float]:
        pass

    @abc.abstractproperty
    def lut_class(self) -> type:
        pass

    def _run_test(self, xshape: Shape, yshape: Shape):
        m = Module()
        m.submodules.dut = dut = self.lut_class(Signal(xshape), Signal(yshape))
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
            yield dut.input.eq(x)
            yield Settle()
            y = yield dut.output
            u = u_x(x)
            v = v_y(y)
            expected_v = self.real_fun(u)
            try:
                self.assertAlmostEqual(v, expected_v, delta=y_precision)
            except AssertionError:
                print(f'x={x} => u={u}')
                print(f'y={y} => v={v}')
                print(f'{self.real_fun.__name__}(u) = {expected_v}')
                raise

        def process():
            for x in range(ShapeMin(xshape), ShapeMax(xshape) + 1):
                with self.subTest(x=x):
                    yield from test_one(x)

        sim.add_process(process)
        sim.run()

    def test_u8(self):
        self._run_test(unsigned(8), unsigned(8))

    def test_i8(self):
        self._run_test(signed(8), signed(8))


class SineLUTTest(SinusoidTestBase, unittest.TestCase):

    @property
    def real_fun(self) -> Callable[[float], float]:
        return math.sin

    @property
    def lut_class(self) -> type:
        return SineLUT


class CosineLUTTest(SinusoidTestBase, unittest.TestCase):

    @property
    def real_fun(self) -> Callable[[float], float]:
        return math.cos

    @property
    def lut_class(self) -> type:
        return CosineLUT


if __name__ == '__main__':
    unittest.main()