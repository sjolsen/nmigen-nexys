from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from bcd import BCDRenderer, BinToBCD
from display import DisplayBank, DisplayMultiplexer, SingleDisplayValue
from nexysa7100t import NexysA7100TPlatform
from srgb import sRGBGammaLUT


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
        m.submodules.b2d = b2d = BinToBCD(
            input=Signal(8),
            output=[Signal(4) for _ in range(4)])
        m.submodules.bcdr = bcdr = BCDRenderer(b2d.output)
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


class ManualBrightness(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Compute left and right binary values using the switches    
        switches = [platform.request('switch', i) for i in range(8)]
        rval_meta = Signal(8)
        m.d.sync += rval_meta.eq(Cat(*switches))
        rval = Signal(8)
        m.d.sync += rval.eq(rval_meta)
        m.submodules.gamma = gamma = sRGBGammaLUT(input=rval, output=Signal(8))
        lval = gamma.output
        # Display raw binary on row LEDs for debugging
        rleds = Cat(*[platform.request('led', i) for i in range(8)])
        lleds = Cat(*[platform.request('led', i) for i in range(8, 16)])
        m.d.comb += rleds.eq(rval)
        m.d.comb += lleds.eq(lval)        
        # Set up the BCD conversion pipeline
        m.submodules.conv = conv = ConversionPipeline(rval, lval)
        rdispval = [SingleDisplayValue(segments=disp, duty_cycle=rval) for disp in conv.rdisp]
        ldispval = [SingleDisplayValue(segments=disp, duty_cycle=lval) for disp in conv.ldisp]
        # Display the output
        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        display = DisplayBank(segments=Signal(8), anodes=Signal(8))
        m.d.comb += segments.eq(display.segments)
        m.d.comb += anodes.eq(display.anodes)
        m.submodules.dispmux = DisplayMultiplexer(
            inputs=Array(rdispval + ldispval),
            output=display)

        return m


if __name__ == "__main__":
    NexysA7100TPlatform().build(ManualBrightness(), do_program=True)