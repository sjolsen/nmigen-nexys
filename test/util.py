"""Utilities for test and simulation."""

from typing import ContextManager, Optional

from nmigen.back.pysim import *


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
            break
        yield


def BazelWriteVCD(
        sim: Simulator, vcd_file: str,
        gtkw_file: Optional[str] = None,
        **kwargs) -> ContextManager[None]:
    """Write VCD outputs to the undeclared outputs directory.

    Bazel tries to run things as hermetically as possible, which causes problems
    when trying to do non-hermetic things like produce test results. Bazel
    provides a directory specifically for this purpose (accessible under
    bazel-testlogs) where test outputs created by this function can be found.
    """
    outdir = os.getenv('TEST_UNDECLARED_OUTPUTS_DIR')
    if outdir is None:
        def outfile(basename):
            return basename
    else:
        def outfile(basename):
            return os.path.join(outdir, basename)
    return sim.write_vcd(
        vcd_file=outfile(vcd_file),
        gtkw_file=outfile(gtkw_file) if gtkw_file is not None else None,
        **kwargs)
