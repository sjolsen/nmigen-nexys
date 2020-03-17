from typing import List

from nmigen import *


def ShapeMin(s: Shape) -> int:
    return -(2**(s.width - 1)) if s.signed else 0


def ShapeMax(s: Shape) -> int:
    return 2**(s.width - 1) - 1 if s.signed else 2**s.width - 1


def ShapeMid(s: Shape) -> int:
    return 0 if s.signed else 2**(s.width - 1)


def Clamp(x: float, shape: Shape) -> int:
    y = int(round(x))
    y = max(y, ShapeMin(shape))
    y = min(y, ShapeMax(shape))
    return y


def Flatten(m: Module, input: List[Signal]) -> Signal:
    cat = Cat(*input)
    flat = Signal(cat.shape())
    m.d.comb += flat.eq(cat)
    return flat
