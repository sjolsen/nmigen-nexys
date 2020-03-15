from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from bcd import BCDRenderer, BinToBCD
from nexysa7100t import NexysA7100TPlatform
from pwm import PWM
from square_fraction import SquareFraction


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
            with m.If(select == i & self.inputs[i].segments.any()):
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


class ConversionPipeline(Elaboratable):

    def __init__(self, rval: Signal, lval: Signal):
        super().__init__()
        self.rval = rval
        self.lval = lval
        self.rdisp = [Signal(8, reset=0) for _ in range(4)]
        self.ldisp = [Signal(8, reset=0) for _ in range(4)]
        self.done = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Intantiate the BCD pipeline
        m.submodules.b2d = b2d = BinToBCD(
            input=Signal(8),
            output=[Signal(4) for _ in range(4)])
        m.submodules.bcdr = bcdr = BCDRenderer(b2d.output)
        m.d.comb += bcdr.start.eq(b2d.done)
        # Set up change detection
        last_input = Signal(17, reset=-1)  # Poison on reset
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
                b2d.start.eq(0)
                with m.If(bcdr.done):
                    m.d.sync += Cat(*self.rdisp).eq(Cat(*bcdr.output))
                    # Use the latched input
                    m.d.sync += b2d.input.eq(last_input[8:16])
                    m.d.sync += b2d.start.eq(1)
                    m.next = 'CONVERT_LEFT'
            with m.State('CONVERT_LEFT'):
                b2d.start.eq(0)
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
        m.submodules.square_fraction = sf = SquareFraction(rval)
        lval = sf.output
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
        segments_o = platform.request('display_7seg')
        anodes_o = platform.request('display_7seg_an')
        segments = Signal(8)
        anodes = Signal(8)
        m.d.comb += segments_o.eq(segments)
        m.d.comb += anodes_o.eq(~anodes)
        display = DisplayBank(segments=segments, anodes=anodes)
        m.submodules.dispmux = DisplayMultiplexer(
            inputs=Array(rdispval + ldispval),
            output=display)

        return m


if __name__ == "__main__":
    NexysA7100TPlatform().build(ManualBrightness(), do_program=True)