from nmigen import *
from nmigen.back.pysim import *
from nmigen.build import *
from nmigen.hdl.rec import *
import sys

from bcd import DigitLUT
from nexysa7100t import NexysA7100TPlatform
from pwm import PWM


class DisplayBank(Record):

    _LAYOUT = Layout([
        ('segments', 8),
        ('anodes', 8),
    ])

    def __init__(self, **kwargs):
        super().__init__(self._LAYOUT, fields=kwargs)


class SingleDisplayValue(Record):

    _LAYOUT = Layout([
        ('segments', 8),
        ('duty_cycle', 8),
    ])

    def __init__(self, **kwargs):
        super().__init__(self._LAYOUT, fields=kwargs)


class DisplayMultiplexer(Elaboratable):

    def __init__(self, inputs: Array, output: DisplayBank):
        super().__init__()
        assert len(inputs) == 8
        self.inputs = inputs
        self.output = output

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Output data + PWM to the display selected by ``select``
        select = Signal(range(8), reset=0)
        m.submodules.pwm = pwm = PWM(Signal(8))
        m.d.comb += pwm.duty_cycle.eq(self.inputs[select].duty_cycle)
        m.d.comb += self.output.segments.eq(self.inputs[select].segments)
        for i in range(8):
            with m.If((select == i) & self.inputs[i].segments.any()):
                m.d.comb += self.output.anodes[i].eq(pwm.output)
            with m.Else():
                m.d.comb += self.output.anodes[i].eq(0)
        # Let the PWM run for 8 steps per display. The resulting refresh rate
        # should be 100 MHz / 256 / 8 ~= 50 kHz.
        strobe_counter = Signal(range(8), reset=0)
        with m.If(pwm.strobe):
            m.d.sync += strobe_counter.eq(strobe_counter + 1)
            with m.If(strobe_counter == 7):
                m.d.sync += select.eq(select + 1)
        return m


class DisplayMultiplexerDemo(Elaboratable):

    def __init__(self, segments, anodes):
        super().__init__
        self.segments = segments
        self.anodes = anodes

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        display_values = []
        for i in range(8):
            val = SingleDisplayValue(segments=Signal(8), duty_cycle=Signal(8))
            m.d.comb += val.segments.eq(DigitLUT.TABLE[i])
            m.d.comb += val.duty_cycle.eq((i * 255) // 7)
            display_values.append(val)            
        # Display the output
        display = DisplayBank(segments=Signal(8), anodes=Signal(8))
        m.d.comb += self.segments.eq(display.segments)
        m.d.comb += self.anodes.eq(display.anodes)
        m.submodules.dispmux = DisplayMultiplexer(
            inputs=Array(display_values),
            output=display)
        return m


if __name__ == "__main__":
    if '--sim' in sys.argv:
        m = Module()
        segments = Signal(8)
        anodes = Signal(8)
        m.submodules.demo = DisplayMultiplexerDemo(segments, anodes)
        sim = Simulator(m)
        sim.add_clock(1e-8)
        with sim.write_vcd("test.vcd", "test.gtkw", traces=[segments, anodes]):
            sim.run_until(100e-6, run_passive=True)
    else:
        platform = NexysA7100TPlatform()
        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        demo = DisplayMultiplexerDemo(segments, anodes)
        platform.build(demo, do_program=True)