from typing import ContextManager, Optional

from nmigen.back.pysim import *


def YieldList(l, result):
    for x in l:
        y = yield x
        result.append(y)


def WaitDone(done):
    while True:
        x = yield done
        if x:
            break
        yield


def BazelWriteVCD(sim: Simulator, vcd_file: str,
                  gtkw_file: Optional[str] = None,
                  *args, **kwargs) -> ContextManager[None]:
    outdir = os.getenv('TEST_UNDECLARED_OUTPUTS_DIR')
    if outdir is None:
        outfile = lambda basename: basename
    else:
        outfile = lambda basename: os.path.join(outdir, basename)
    return sim.write_vcd(
        vcd_file=outfile(vcd_file),
        gtkw_file=outfile(gtkw_file) if gtkw_file is not None else None,
        *args, **kwargs)
