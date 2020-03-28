"""Demo for comparing gamma LUTS."""

from absl import app
from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.board.nexysa7100t import manual_brightness
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.color import srgb
from nmigen_nexys.core import top
from nmigen_nexys.display import seven_segment


class ManualBrightness(Elaboratable):
    """Demo for comparing gamma curves.

    This demo splits the seven-segment display bank into two halves of four. The
    eight rightmost switches are used to specify a binary number used as a raw
    brightness setting. This raw setting is used to set the brightness of the
    right half directly, and is passed through a gamma LUT before setting the
    brightness of the left half.

    Each half of the bank displays the value used as its PWM duty cycle (i.e.
    after the LUT on the left-hand side). This value is displayed in decimal,
    and as such this demo also serves to demonstrate the binary-to-BCD and
    BCD display conversion pipelines.
    """

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Compute left and right binary values using the switches
        switches = [platform.request('switch', i) for i in range(8)]
        rval_meta = Signal(8)
        m.d.sync += rval_meta.eq(Cat(*switches))
        rval = Signal(8)
        m.d.sync += rval.eq(rval_meta)
        m.submodules.gamma = gamma = srgb.sRGBGammaLUT(
            input=rval, output=Signal(8))
        lval = gamma.output
        # Display raw binary on row LEDs for debugging
        rleds = Cat(*[platform.request('led', i) for i in range(8)])
        lleds = Cat(*[platform.request('led', i) for i in range(8, 16)])
        m.d.comb += rleds.eq(rval)
        m.d.comb += lleds.eq(lval)
        # Set up the BCD conversion pipeline
        m.submodules.conv = conv = manual_brightness.ConversionPipeline(
            rval, lval)
        rdispval = [seven_segment.SingleDisplayValue(
            segments=disp, duty_cycle=rval) for disp in conv.rdisp]
        ldispval = [seven_segment.SingleDisplayValue(
            segments=disp, duty_cycle=lval) for disp in conv.ldisp]
        # Display the output
        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        display = seven_segment.DisplayBank(
            segments=Signal(8), anodes=Signal(8))
        m.d.comb += segments.eq(display.segments)
        m.d.comb += anodes.eq(display.anodes)
        m.submodules.dispmux = seven_segment.DisplayMultiplexer(
            inputs=Array(rdispval + ldispval),
            output=display)

        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), ManualBrightness())

if __name__ == "__main__":
    app.run(main)
