"""Utilities for test and simulation."""

import os


SIMULATION_CLOCK_FREQUENCY = 100_000_000


def YieldList(l, result):
    """Yield a list of signals into result.

    result should be empty on entry. This is an input parameter instead of the
    return value because implementing YieldList as a generator makes the return
    value unavailable.
    """
    for x in l:
        y = yield x
        result.append(y)


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
