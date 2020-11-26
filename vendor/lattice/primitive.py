from typing import Optional

from nmigen import *
from nmigen.build import Platform


class EHXPLLL(Elaboratable):

    def __init__(self, *,
                 clki_div: Optional[int] = None,
                 clkfb_div: Optional[int] = None,
                 clkop_div: Optional[int] = None):
        super().__init__()
        # Parameters
        self.clki_div = clki_div
        self.clkfb_div = clkfb_div
        self.clkop_div = clkop_div
        # Ports
        self.clki = Signal()
        # self.clki2 = Signal()
        # self.sel = Signal()
        self.clkfb = Signal()
        # self.phasesel = Signal(2)
        # self.phasedir = Signal()
        # self.phasestep = Signal()
        # self.phaseloadreg = Signal()
        self.clkop = Signal()
        self.clkos = Signal()
        self.clkos2 = Signal()
        self.clkos3 = Signal()
        self.lock = Signal()
        self.stdby = Signal()
        self.rst = Signal()
        self.enclkop = Signal()
        self.enclkos = Signal()
        self.enclkos2 = Signal()
        self.enclkos3 = Signal()

    def elaborate(self, _: Optional[Platform]) -> Fragment:
        f = Fragment()
        params = [
            ('p', 'CLKI_DIV', self.clki_div),
            ('p', 'CLKFB_DIV', self.clkfb_div),
            ('p', 'CLKOP_DIV', self.clkop_div),
        ]
        ports = [
            ('i', 'CLKI ', self.clki),
            # ('i', 'CLKI2 ', self.clki2),
            # ('i', 'SEL ', self.sel),
            ('i', 'CLKFB ', self.clkfb),
            # ('i', 'PHASESEL ', self.phasesel),
            # ('i', 'PHASEDIR', self.phasedir),
            # ('i', 'PHASESTEP', self.phasestep),
            # ('i', 'PHASELOADREG ', self.phaseloadreg),
            ('o', 'CLKOP ', self.clkop),
            ('o', 'CLKOS ', self.clkos),
            ('o', 'CLKOS2 ', self.clkos2),
            ('o', 'CLKOS3 ', self.clkos3),
            ('o', 'LOCK ', self.lock),
            ('i', 'STDBY ', self.stdby),
            ('i', 'RST ', self.rst),
            ('i', 'ENCLKOP ', self.enclkop),
            ('i', 'ENCLKOS ', self.enclkos),
            ('i', 'ENCLKOS2 ', self.enclkos2),
            ('i', 'ENCLKOS3 ', self.enclkos3),
        ]
        f.add_subfragment(Instance(
            'EHXPLLL',
            *params,
            *ports,
        ))
        return f
