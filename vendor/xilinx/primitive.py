from typing import Optional

from nmigen import *
from nmigen.build import Platform


class BscanE2(Elaboratable):

    def __init__(self, jtag_chain: int = 1):
        super().__init__()
        # Parameters
        self.jtag_chain = jtag_chain
        # Ports
        self.capture = Signal(1)
        self.drck = Signal(1)
        self.reset = Signal(1)
        self.runtest = Signal(1)
        self.sel = Signal(1)
        self.shift = Signal(1)
        self.tck = Signal(1)
        self.tdi = Signal(1)
        self.tms = Signal(1)
        self.update = Signal(1)
        self.tdo = Signal(1)

    def elaborate(self, _: Optional[Platform]) -> Fragment:
        f = Fragment()
        params = [
            ('p', 'JTAG_CHAIN', self.jtag_chain),
        ]
        ports = [
            ('o', 'CAPTURE', self.capture),
            ('o', 'DRCK', self.drck),
            ('o', 'RESET', self.reset),
            ('o', 'RUNTEST', self.runtest),
            ('o', 'SEL', self.sel),
            ('o', 'SHIFT', self.shift),
            ('o', 'TCK', self.tck),
            ('o', 'TDI', self.tdi),
            ('o', 'TMS', self.tms),
            ('o', 'UPDATE', self.update),
            ('i', 'TDO', self.tdo),
        ]
        f.add_subfragment(Instance(
            'BSCANE2',
            *params,
            *ports,
        ))
        return f
