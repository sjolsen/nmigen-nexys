"""Language-level utilities for nMigen."""

from typing import Iterable, List, Optional, TypeVar

from nmigen import *
from nmigen.hdl.ast import Assign
from nmigen.utils import log2_int


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


def NMux(select: Signal, signals: List[Signal]) -> Value:
    """Multiplex arbitrarily many signals."""
    assert len(signals) != 0
    if len(signals) == 1:
        return signals[0]
    nbits = log2_int(len(signals), need_pow2=False)
    midpoint = (1 << nbits) // 2
    low = signals[:midpoint]
    high = signals[midpoint:]
    return Mux(select[nbits - 1], NMux(select[:nbits - 1], high),
               NMux(select[:nbits - 1], low))


T = TypeVar('T')
def Multiplex(select: Signal, root: T, leaves: List[T], fan_in: List[str],
              fan_out: List[str]) -> Iterable[Assign]:
    """Multiplex entire objects.

    T may contain both input and output signals. Signals listed under fan_in are
    multiplexed from the leaves to the root using select. Signals listed under
    fan_out are propagated unconditionally from the root to the leaves.
    """
    for field in fan_in:
        dst = getattr(root, field)
        srcs = [getattr(leaf, field) for leaf in leaves]
        yield dst.eq(NMux(select, srcs))
    for field in fan_out:
        src = getattr(root, field)
        dsts = [getattr(leaf, field) for leaf in leaves]
        yield Cat(*dsts).eq(Repl(src, len(dsts)))
