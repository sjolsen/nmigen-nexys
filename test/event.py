from typing import Any, Callable, Iterable, List, NamedTuple, Optional, Union
import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import edge
from nmigen_nexys.core import util
from nmigen_nexys.test import test_util


Event = Any  # TODO: Maybe a protocol type?


class TimestampedEvent(NamedTuple):
    cycle: int
    event: Event


class EdgeEvent(NamedTuple):
    """Simulation event: GPIO toggled."""
    signal: Signal
    direction: str  # TODO(python-3.8): Literal['rose', 'fell']


def edge_monitor(detectors: Iterable[edge.Detector],
                 cycle_counter: Signal,
                 callback: Callable[[TimestampedEvent], None]) \
        -> test_util.CoroutineProcess[None]:
    def _edge_monitor():
        yield Passive()
        while True:
            yield
            for detector in detectors:
                cycle = yield cycle_counter
                if (yield detector.rose):
                    event = EdgeEvent(detector.input, 'rose')
                    callback(TimestampedEvent(cycle, event))
                if (yield detector.fell):
                    event = EdgeEvent(detector.input, 'fell')
                    callback(TimestampedEvent(cycle, event))
    return _edge_monitor


def ShowEvents(sim_events: List[TimestampedEvent]):
    if not sim_events:
        print('No simulation events captured')
        return
    dbg_table = []
    for e1, e2 in zip([None] + sim_events[:-1], sim_events):
        diff = f'({e2.cycle - e1.cycle:+})' if e1 else ' '
        dbg_table.append((str(e2.cycle), diff, repr(e2.event)))
    widths = [max(len(row[col]) for row in dbg_table) for col in range(2)]
    dbg_out = ['Simulation events:']
    for ts, diff, disp in dbg_table:
        dbg_out.append(f'  {ts:>{widths[0]}} {diff:>{widths[1]}} {disp}')
    print('\n'.join(dbg_out))


class DelayConstraint(object):

    def __init__(self, *, seconds: Optional[float] = None,
                 cycles: Optional[int] = None):
        super().__init__()
        if seconds is not None:
            assert cycles is None
            self.cycles = int(seconds * util.SIMULATION_CLOCK_FREQUENCY)
        else:
            assert cycles is not None
            self.cycles = cycles


class MinDelay(DelayConstraint):
    pass


class MaxDelay(DelayConstraint):
    pass


EventConstraints = Iterable[Union[Event, DelayConstraint]]


def ValidateConstraints(tc: unittest.TestCase,
                        actual: Iterable[TimestampedEvent],
                        expected: EventConstraints):
    actual_iter = iter(actual)
    last_ts = 0
    delay_constraints = []
    for constraint in expected:
        if isinstance(constraint, DelayConstraint):
            delay_constraints.append(constraint)
            continue
        event = next(actual_iter)
        # tc.assertIsInstance(constraint, Event)
        tc.assertEqual(event.event, constraint)
        if delay_constraints:
            total = sum(c.cycles for c in delay_constraints)
            if all(isinstance(c, MinDelay) for c in delay_constraints):
                tc.assertGreaterEqual(event.cycle - last_ts, total)
            elif all(isinstance(c, MinDelay) for c in delay_constraints):
                tc.assertGreaterEqual(event.cycle - last_ts, total)
            else:
                tc.fail('Invalid mix of delay constraints')
            delay_constraints = []
        last_ts = event.cycle
