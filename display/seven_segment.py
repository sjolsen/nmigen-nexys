from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import pwm as pwm_module


class DigitLUT(Elaboratable):

    # 7-bit encoding of segments A-G, indexed by value
    TABLE = [
        0b0111111,
        0b0000110,
        0b1011011,
        0b1001111,
        0b1100110,
        0b1101101,
        0b1111101,
        0b0000111,
        0b1111111,
        0b1101111,
    ]

    def __init__(self, input: Signal):
        super().__init__()
        self.input = input
        self.output = Signal(8)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        with m.Switch(self.input):
            for i, val in enumerate(self.TABLE):
                with m.Case(i):
                    m.d.comb += self.output.eq(val)
            with m.Case():
                m.d.comb += self.output.eq(0)
        return m


class BCDRenderer(Elaboratable):

    def __init__(self, input: [Signal]):
        super().__init__()
        assert len(input) != 0
        self.input = input
        self.start = Signal(reset=0)
        self.output = [Signal(8) for _ in input]
        self.done = Signal(reset=0)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        input = Signal(4 * len(self.input))
        current_input = input[-4:]
        output = Cat(*self.output)
        current_output = Signal(8)
        cursor = Signal(range(len(self.input)), reset=len(self.input) - 1)
        seen_nonzero = Signal()
        m.submodules.lut = lut = DigitLUT(current_input)
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += input.eq(Cat(*self.input))
                    m.d.sync += cursor.eq(cursor.reset)
                    m.d.sync += seen_nonzero.eq(0)
                    m.next = 'CONVERT'
            with m.State('CONVERT'):
                is_zero = (current_input == 0).bool()
                leading_zero = ~seen_nonzero.bool() & is_zero
                blank_zero = leading_zero & (cursor != 0).bool()
                with m.If(blank_zero):
                    m.d.comb += current_output.eq(0)
                with m.Else():
                    m.d.comb += current_output.eq(lut.output)
                m.d.sync += cursor.eq(cursor - 1)
                m.d.sync += seen_nonzero.eq(seen_nonzero | ~is_zero)
                with m.If(cursor == 0):
                    m.next = 'DONE'
                    m.d.sync += self.done.eq(1)
                m.d.sync += input.eq(input << 4)
                m.d.sync += output.eq(Cat(current_output, output[:-8]))
            with m.State('DONE'):
                m.d.sync += self.done.eq(0)
                m.next = 'IDLE'
        return m


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
        m.submodules.pwm = pwm = pwm_module.PWM(Signal(8))
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
