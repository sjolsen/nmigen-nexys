from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.display import seven_segment
from nmigen_nexys.math import bcd


class ConversionPipeline(Elaboratable):

    def __init__(self, rval: Signal, lval: Signal):
        super().__init__()
        self.rval = rval
        self.lval = lval
        self.rdisp = [Signal(8, reset=0) for _ in range(4)]
        self.ldisp = [Signal(8, reset=0) for _ in range(4)]
        self.done = Signal(reset=0)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Intantiate the BCD pipeline
        m.submodules.b2d = b2d = bcd.BinToBCD(
            input=Signal(8),
            output=[Signal(4) for _ in range(4)])
        m.submodules.bcdr = bcdr = seven_segment.BCDRenderer(b2d.output)
        m.d.comb += bcdr.start.eq(b2d.done)
        # Set up change detection
        last_input = Signal(17, reset=2**16)  # Poison on reset
        current_input = Signal(17)
        m.d.comb += current_input.eq(Cat(self.rval, self.lval, C(0, 1)))
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(last_input != current_input):
                    m.d.sync += last_input.eq(current_input)
                    m.d.sync += b2d.input.eq(current_input[0:8])
                    m.d.sync += b2d.start.eq(1)
                    m.next = 'CONVERT_RIGHT'
            with m.State('CONVERT_RIGHT'):
                m.d.sync += b2d.start.eq(0)
                with m.If(bcdr.done):
                    m.d.sync += Cat(*self.rdisp).eq(Cat(*bcdr.output))
                    # Use the latched input
                    m.d.sync += b2d.input.eq(last_input[8:16])
                    m.d.sync += b2d.start.eq(1)
                    m.next = 'CONVERT_LEFT'
            with m.State('CONVERT_LEFT'):
                m.d.sync += b2d.start.eq(0)
                with m.If(bcdr.done):
                    m.d.sync += Cat(*self.ldisp).eq(Cat(*bcdr.output))
                    m.d.sync += self.done.eq(1)
                    m.next = 'DONE'
            with m.State('DONE'):
                m.d.sync += self.done.eq(0)
                m.next = 'IDLE'
        return m
