"""Language-level utilities for nMigen."""

from typing import List, Optional

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


def SatAdd(a: Signal, b: int, limit: Optional[int] = None) -> Value:
    """Saturating addition.

    The result is clamped to max, which defaults to the maximum value
    representable in a.
    """
    if limit is None:
        limit = ShapeMax(a.shape())
    return Mux(a <= limit - b, a + b, limit)


def SatSub(a: Signal, b: int, limit: Optional[int] = None) -> Value:
    """Saturating subtraction.

    The result is clamped to limit, which defaults to the minimum value
    representable in a.
    """
    if limit is None:
        limit = ShapeMin(a.shape())
    return Mux(a >= limit + b, a - b, limit)


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
