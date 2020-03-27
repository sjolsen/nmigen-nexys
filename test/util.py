"""Utilities for test and simulation."""

import os


SIMULATION_CLOCK_FREQUENCY = 100_000_000


def YieldList(l):
    """Yield a list of signals into result."""
    result = []
    for x in l:
        y = yield x
        result.append(y)
    return result


def WaitDone(done):
    """Perform synchronous yields until done is non-zero."""
    while True:
        x = yield done
        if x:
            return x
        yield


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
