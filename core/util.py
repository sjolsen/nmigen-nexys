"""Language-level utilities for nMigen."""

from typing import List

from nmigen import *


def ShapeMin(s: Shape) -> int:
    """The minimum value representable by s."""
    return -(2**(s.width - 1)) if s.signed else 0


def ShapeMax(s: Shape) -> int:
    """The maximum value representable by s."""
    return 2**(s.width - 1) - 1 if s.signed else 2**s.width - 1


def ShapeMid(s: Shape) -> int:
    """The medial value representable by s.

    For signed shapes, this is zero. For unsigned shapes, this is
    2**(s.width - 1).
    """
    return 0 if s.signed else 2**(s.width - 1)


def Clamp(x: float, shape: Shape) -> int:
    """Clamp a floating-point constant to the range respresentable by shape.

    TODO: Refactor this into more reusable components.
    """
    y = int(round(x))
    y = max(y, ShapeMin(shape))
    y = min(y, ShapeMax(shape))
    return y


def Flatten(m: Module, input: List[Signal]) -> Signal:
    """Create a signal from the concatenation of the input signals."""
    cat = Cat(*input)
    flat = Signal(cat.shape())
    m.d.comb += flat.eq(cat)
    return flat
