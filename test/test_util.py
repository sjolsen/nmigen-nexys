"""Utilities for test and simulation."""

import os
from typing import Generator, Union, TypeVar
import unittest

from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.core import util


T = TypeVar('T', covariant=True)
CoroutineProcess = Generator[
    Union[Value, Command, None],  # Yield
    int,  # Send (i.e. result of yield)
    T,  # Return
]


class Timer(Elaboratable):

    def __init__(self, tc: unittest.TestCase, timeout_s: float):
        super().__init__()
        self.tc = tc
        self.timeout_s = timeout_s
        self.cycle_counter = Signal(
            range(int(timeout_s * util.SIMULATION_CLOCK_FREQUENCY)),
            reset=0)

    def elaborate(self, _: None) -> Module:
        m = Module()
        m.d.sync += self.cycle_counter.eq(self.cycle_counter + 1)
        return m

    def timeout_process(self) -> CoroutineProcess[None]:
        yield Passive()
        seconds = self.timeout_s
        yield Delay(seconds)
        if seconds >= 1:
            self.tc.fail(f'Test timed out after {seconds} s')
        elif seconds >= 1e-3:
            self.tc.fail(f'Test timed out after {seconds * 1e3} ms')
        elif seconds >= 1e-6:
            self.tc.fail(f'Test timed out after {seconds * 1e6} us')
        elif seconds >= 1e-9:
            self.tc.fail(f'Test timed out after {seconds * 1e9} ns')
        else:
            self.tc.fail(f'Test timed out after {seconds * 1e12} ps')


def YieldList(l):
    """Yield a list of signals into result."""
    result = []
    for x in l:
        y = yield x
        result.append(y)
    return result


def WaitSync(signal: Signal):
    """Perform synchronous yields until signal is non-zero."""
    while True:
        x = yield signal
        if x:
            return x
        yield


# TODO: This should be handled by nMigen itself, by descheduling the process
# until some event occurs.
def WaitEdge(signal):
    """Wait asynchronously for a rising or falling edge on signal."""
    last = None
    while True:
        current = yield signal
        edge = last is not None and current != last
        if edge:
            return current
        last = current
        yield Delay(0.1 * (1 / util.SIMULATION_CLOCK_FREQUENCY))


# TODO: This should be handled by nMigen itself, by descheduling the process
# until some event occurs.
def WaitNegedge(signal):
    """Wait asynchronously for a falling edge on signal."""
    last = None
    while True:
        current = yield signal
        edge = last is not None and current < last
        if edge:
            return current
        last = current
        yield Delay(0.1 * (1 / util.SIMULATION_CLOCK_FREQUENCY))


def BazelTestOutput(path):
    """Make path relative to the test output dir, if it exists.

    Bazel tries to run things as hermetically as possible, which causes problems
    when trying to do non-hermetic things like produce test results. Bazel
    provides a directory specifically for this purpose (accessible under
    bazel-testlogs) where test outputs can be found.
    """
    outdir = os.getenv('TEST_UNDECLARED_OUTPUTS_DIR')
    if outdir is None:
        return path
    else:
        return os.path.join(outdir, path)
