"""Tools for seven-segment display banks."""

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import pwm as pwm_module
from nmigen_nexys.math import lut


class DigitLUT(lut.FunctionLUT):
    """Maps decimal digits to their seven-segment encoding."""

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
        super().__init__(
            lambda i: self.TABLE[i] if i < 10 else 0,
            input=input,
            output=Signal(8, name='output'))


class HexDigitLUT(lut.FunctionLUT):
    """Maps hexadecimal digits to their seven-segment encoding."""

    # 7-bit encoding of segments A-G, indexed by value
    TABLE = DigitLUT.TABLE + [
        0b1110111,
        0b1111100,
        0b0111001,
        0b1011110,
        0b1111001,
        0b1110001,
    ]

    def __init__(self):
        super().__init__(
            self.TABLE.__getitem__,
            input=Signal(4, name='input'),
            output=Signal(8, name='output'))


class BCDRenderer(Elaboratable):
    """Render multiple BCD digits, omitting leading zeros."""

    def __init__(self, input: [Signal]):
        super().__init__()
        assert len(input) != 0
        self.input = input
        self.start = Signal(reset=0)
        self.output = [Signal(8) for _ in input]
        self.done = Signal(reset=0)

    def elaborate(self, _: Platform) -> Module:
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
    """Output signal record for a bank of eight common-anode displays."""

    _LAYOUT = Layout([
        ('segments', 8),
        ('anodes', 8),
    ])

    def __init__(self, **kwargs):
        super().__init__(self._LAYOUT, fields=kwargs)


class SingleDisplayValue(Record):
    """Request record for the pattern and PWM duty cycle for a single display.

    This specifies how ArrayDisplayMultiplexer should drive one of the displays in
    its display bank.
    """

    _LAYOUT = Layout([
        ('segments', 8),
        ('duty_cycle', 8),
    ])

    def __init__(self, **kwargs):
        super().__init__(self._LAYOUT, fields=kwargs)


class DisplayMultiplexer(Elaboratable):

    def __init__(self, output: DisplayBank,
                 num_segments: int = 8, pwm_width: int = 8):
        super().__init__()
        self.output = output
        self.num_segments = num_segments
        self.pwm_width = pwm_width
        self.segments = Signal(8)
        self.duty_cycle = Signal(pwm_width)
        self.select = Signal(range(num_segments), reset=0)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        # Output data + PWM to the display selected by ``select``
        m.submodules.pwm = pwm = pwm_module.PWM(Signal(self.pwm_width))
        m.d.comb += pwm.duty_cycle.eq(self.duty_cycle)
        m.d.comb += self.output.segments.eq(self.segments)
        for i in range(self.num_segments):
            with m.If((self.select == i) & self.segments.any()):
                m.d.comb += self.output.anodes[i].eq(pwm.output)
            with m.Else():
                m.d.comb += self.output.anodes[i].eq(0)
        # Let the PWM run for 8 steps per display. The resulting refresh rate
        # should be 100 MHz / 256 / 8 ~= 50 kHz.
        strobe_counter = Signal(range(8), reset=0)
        with m.If(pwm.strobe):
            m.d.sync += strobe_counter.eq(strobe_counter + 1)
            with m.If(strobe_counter == 7):
                m.d.sync += self.select.eq(self.select + 1)
        return m


class ArrayDisplayMultiplexer(Elaboratable):
    """Multiplex a bank of eight common-anode seven-segment displays.

    Arbitrary patterns are supported and can be generated by BCDRenderer. The
    multiplexer also supports individual PWM duty cycle for each display in the
    bank.
    """

    def __init__(self, inputs: Array, output: DisplayBank):
        super().__init__()
        assert len(inputs) == 8
        self.inputs = inputs
        self.output = output

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.submodules.mux = mux = DisplayMultiplexer(self.output)
        m.d.comb += mux.segments.eq(self.inputs[mux.select].segments)
        m.d.comb += mux.duty_cycle.eq(self.inputs[mux.select].duty_cycle)
        return m


class DisplayMultiplexerDemo(Elaboratable):
    """Simple demo for the display multiplexer.

    This demo displays a static pattern. Each display in the bank displays its
    index (in decimal) and uses the same index as its PWM duty cycle (in
    increments of 12.5%).
    """

    def __init__(self, segments, anodes):
        super().__init__()
        self.segments = segments
        self.anodes = anodes

    def elaborate(self, _: Platform) -> Module:
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
        m.submodules.dispmux = ArrayDisplayMultiplexer(
            inputs=Array(display_values),
            output=display)
        return m
