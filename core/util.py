"""Language-level utilities for nMigen."""

import inspect
import typing
from typing import Iterable, List, Optional, Tuple, Union

from nmigen import *
from nmigen.build import Platform
from nmigen.hdl.ast import Assign
from nmigen.hdl.rec import Direction, Layout, Record
from nmigen.utils import log2_int


SIMULATION_CLOCK_FREQUENCY = 100_000_000


def LikeNamedTuple(nt: Union[str, typing.NamedTupleMeta]) -> type:
    if isinstance(nt, str):
        return typing.ForwardRef(f'LikeNamedTuple({nt})')
    field_types = tuple(nt.__annotations__[f] for f in nt._fields)
    return Union[nt, Tuple.__getitem__(field_types)]


def ProductRepr(obj: object) -> str:
    """Common __repr__ implementation for simple product types.

    ProductRepr assumes the non-self arguments to the object's type's __init__
    method correspond to properties on the object. It uses the name of the type,
    the names of those properties, and the values of those properties to render
    the object. If there is only one property, the name is omitted for brevity.
    For example:

        StartCommand(address=127, data=5)
        StopCommand(1)

    This function is particularly useful for generating FSM strings that are
    rendered in GTKWave.
    """
    # Use the non-self constructor arguments
    params = inspect.getfullargspec(type(obj).__init__).args[1:]
    clsname = type(obj).__name__
    if len(params) > 1:
        args = [f'{p}={getattr(obj, p)}' for p in params]
    else:
        args = [f'{getattr(obj, p)}' for p in params]
    return f'{clsname}({", ".join(args)})'


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


def Any(values: Iterable[Value]) -> Value:
    return Cat(*values).any()


def GetClockFreq(platform: Optional[Platform]) -> int:
    """Get the clock frequency for the sync domain.

    This is meant to provide a uniform API between synthesis and simulation.
    When used in simulation, the simulation object should be given a clock of
    SIMULATION_CLOCK_FREQUENCY.
    """
    if platform is not None:
        return int(platform.default_clk_frequency)
    return SIMULATION_CLOCK_FREQUENCY


class MultiplexError(Exception):
    """Logic error in the construction of NMux or Multiplex."""


def NMux(select: Signal, signals: List[Signal]) -> Value:
    """Multiplex arbitrarily many signals."""
    if len(signals) == 0:
        raise MultiplexError('Cannot mux zero signals')
    if len(signals) == 1:
        return signals[0]
    nbits = log2_int(len(signals), need_pow2=False)
    midpoint = (1 << nbits) // 2
    low = signals[:midpoint]
    high = signals[midpoint:]
    return Mux(select[nbits - 1], NMux(select[:nbits - 1], high),
               NMux(select[:nbits - 1], low))


def Multiplex(select: Signal, root: Record,
              leaves: List[Record]) -> Iterable[Assign]:
    """Multiplex entire objects.

    Fan-in signals are multiplexed from the leaves to the root using select.
    Fan-out signals are propagated unconditionally from the root to the leaves.
    """
    for field, (shape, direction) in root.layout.fields.items():
        sub_root = getattr(root, field)
        sub_leaves = [getattr(leaf, field) for leaf in leaves]
        if isinstance(shape, Layout):
            yield from Multiplex(select, sub_root, sub_leaves)
        elif direction == Direction.FANIN:
            yield sub_root.eq(NMux(select, sub_leaves))
        elif direction == Direction.FANOUT:
            yield Cat(*sub_leaves).eq(Repl(sub_root, len(sub_leaves)))
        else:
            raise MultiplexError(
                f'Could not multiplex field {field} with shape {shape} and '
                f'direction {direction}')
