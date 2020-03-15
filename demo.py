import itertools
from nmigen import *
from nmigen.build import *

from nexysa7100t import NexysA7100TPlatform
from square_fraction import SquareFraction


class Timer(Elaboratable):

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.triggered = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = Signal(range(self.period), reset=self.period - 1)
        m.d.comb += self.triggered.eq(counter == 0)
        with m.If(counter == 0):
            m.d.sync += counter.eq(counter.reset)
        with m.Else():
            m.d.sync += counter.eq(counter - 1)
        return m


class PWM(Elaboratable):

    def __init__(self, duty_cycle: Signal):
        super().__init__()
        self.duty_cycle = duty_cycle
        self.output = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = Signal(self.duty_cycle.width, reset=0)
        m.d.sync += counter.eq(counter + 1)
        m.d.comb += self.output.eq(counter > self.duty_cycle)
        return m


class TriangleWave(Elaboratable):

    def __init__(self, period: int, precision: int):
        super().__init__()
        self.period = period
        self.precision = precision
        self.output = Signal(precision)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        counter = Signal(range(self.period), reset=0)
        m.d.sync += counter.eq(counter + 1)
        half_wave = counter[-1]
        high_bits = counter[-1 - self.precision : -1]
        with m.If(half_wave == 0):
            m.d.comb += self.output.eq(high_bits)
        with m.Else():
            m.d.comb += self.output.eq(C(-1, len(high_bits)) - high_bits)
        return m


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        clk_period = int(platform.default_clk_frequency)
        m.submodules.timer = timer = Timer(clk_period // 2)
        m.submodules.triangle = triangle = TriangleWave(10 * clk_period, 8)
        m.submodules.square_fracion = sf = SquareFraction(triangle.output)
        m.submodules.pwm = pwm = PWM(sf.output)

        segments = platform.request('display_7seg')
        anodes = platform.request('display_7seg_an')
        m.d.comb += anodes.eq(Repl(pwm.output, 8))

        shift_register = Signal(8, reset=0b11110000)
        with m.If(timer.triggered):
            m.d.sync += shift_register.eq(
                shift_register << 1 | shift_register >> 7)

        m.d.comb += segments.eq(shift_register)

        return m


if __name__ == "__main__":
    NexysA7100TPlatform().build(Demo(), do_program=True)