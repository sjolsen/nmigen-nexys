from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.board.nexysa7100t import manual_brightness
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.color import srgb
from nmigen_nexys.display import seven_segment
from nmigen_nexys.math import bcd


class ManualBrightness(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Compute left and right binary values using the switches    
        switches = [platform.request('switch', i) for i in range(8)]
        rval_meta = Signal(8)
        m.d.sync += rval_meta.eq(Cat(*switches))
        rval = Signal(8)
        m.d.sync += rval.eq(rval_meta)
        m.submodules.gamma = gamma = srgb.sRGBGammaLUT(input=rval, output=Signal(8))
        lval = gamma.output
        # Display raw binary on row LEDs for debugging
        rleds = Cat(*[platform.request('led', i) for i in range(8)])
        lleds = Cat(*[platform.request('led', i) for i in range(8, 16)])
        m.d.comb += rleds.eq(rval)
        m.d.comb += lleds.eq(lval)        
        # Set up the BCD conversion pipeline
        m.submodules.conv = conv = manual_brightness.ConversionPipeline(rval, lval)
        rdispval = [seven_segment.SingleDisplayValue(segments=disp, duty_cycle=rval) for disp in conv.rdisp]
        ldispval = [seven_segment.SingleDisplayValue(segments=disp, duty_cycle=lval) for disp in conv.ldisp]
        # Display the output
        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        display = seven_segment.DisplayBank(segments=Signal(8), anodes=Signal(8))
        m.d.comb += segments.eq(display.segments)
        m.d.comb += anodes.eq(display.anodes)
        m.submodules.dispmux = seven_segment.DisplayMultiplexer(
            inputs=Array(rdispval + ldispval),
            output=display)

        return m


if __name__ == "__main__":
    nexysa7100t.NexysA7100TPlatform().build(ManualBrightness(), do_program=True)
