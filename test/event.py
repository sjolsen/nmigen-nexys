import abc
from typing import Any, Generator, Iterable, List, NamedTuple, Optional, Union
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


class EventSeries(object):

    def __init__(self, cycle_counter: Signal):
        super().__init__()
        self._cycle_counter = cycle_counter
        self._events: List[TimestampedEvent] = []

    def add(self, event: Event) -> Generator[None, Signal, int]:
        cycle = yield self._cycle_counter
        self._events.append(TimestampedEvent(cycle, event))

    def ShowEvents(self):
        if not self._events:
            print('No simulation events captured')
            return
        dbg_table = []
        for e1, e2 in zip([None] + self._events[:-1], self._events):
            diff = f'({e2.cycle - e1.cycle:+})' if e1 else ' '
            dbg_table.append((str(e2.cycle), diff, repr(e2.event)))
        widths = [max(len(row[col]) for row in dbg_table) for col in range(2)]
        dbg_out = ['Simulation events:']
        for ts, diff, disp in dbg_table:
            dbg_out.append(f'  {ts:>{widths[0]}} {diff:>{widths[1]}} {disp}')
        print('\n'.join(dbg_out))

    def ValidateConstraints(self, tc: unittest.TestCase,
                            expected: EventConstraints):
        actual_iter = iter(self._events)
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


class Monitor(abc.ABC):

    def __init__(self):
        super().__init__()
        self._event_series = None

    def emit(self, event: Event) -> Generator[None, Signal, int]:
        yield from self._event_series.add(event)

    @abc.abstractmethod
    def process(self) -> test_util.CoroutineProcess[None]:
        pass

    def attach(self, sim: Simulator, event_series: EventSeries):
        self._event_series = event_series
        sim.add_sync_process(self.process)


class EdgeMonitor(Monitor):

    def __init__(self, detectors: Iterable[edge.Detector]):
        super().__init__()
        self._detectors = detectors

    def process(self) -> test_util.CoroutineProcess[None]:
        yield Passive()
        while True:
            yield
            for detector in self._detectors:
                if (yield detector.rose):
                    yield from self.emit(EdgeEvent(detector.input, 'rose'))
                if (yield detector.fell):
                    yield from self.emit(EdgeEvent(detector.input, 'fell'))
