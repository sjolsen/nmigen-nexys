"""Shift register implementations."""

import abc

from nmigen import *
from nmigen.build import *


class Register(Elaboratable):
    """Common interface for up- and down-shifting registers.

    The entire contents of the shift register can be written from word_in by
    strobing latch. One bit can be shifted in/out by strobing shift. The latch
    signal takes precedence over the shift signal.
    """

    def __init__(self, width: int, reset: int = 0):
        super().__init__()
        self.width = width
        self.reset = reset
        self.word_in = Signal(width)
        self.word_out = Signal(width)
        self.latch = Signal()
        self.bit_in = Signal()
        self.bit_out = Signal()
        self.shift = Signal()

    @abc.abstractmethod
    def elaborate(self, _: Platform) -> Module:
        pass


class Up(Register):
    """Up- or left-shifting register."""

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        reg = Signal(self.width, reset=self.reset)
        m.d.comb += self.word_out.eq(reg)
        m.d.comb += self.bit_out.eq(reg[-1])
        with m.If(self.latch):
            m.d.sync += reg.eq(self.word_in)
        with m.Elif(self.shift):
            m.d.sync += reg.eq(Cat(self.bit_in, reg[:-1]))
        return m


class Down(Register):
    """Down- or right-shifting register."""

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        reg = Signal(self.width, reset=self.reset)
        m.d.comb += self.word_out.eq(reg)
        m.d.comb += self.bit_out.eq(reg[0])
        with m.If(self.latch):
            m.d.sync += reg.eq(self.word_in)
        with m.Elif(self.shift):
            m.d.sync += reg.eq(Cat(reg[1:], self.bit_in))
        return m


class ArrayRegister(Elaboratable):
    """Common interface for up- and down-shifting array registers."""

    def __init__(self, *, width: int, count: int, reset: int = 0):
        super().__init__()
        self.width = width
        self.count = count
        self.reset = reset
        self.words_in = Array([Signal(width) for _ in range(count)])
        self.words_out = Array([Signal(width) for _ in range(count)])
        self.latch = Signal()
        self.word_in = Signal(width)
        self.shift = Signal()

    @abc.abstractmethod
    def elaborate(self, _: Platform) -> Module:
        pass


class ArrayUp(ArrayRegister):
    """Up- or left-shifting register."""

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        reg = Signal(self.width * self.count, reset=self.reset)
        m.d.comb += Cat(*self.words_out).eq(reg)
        with m.If(self.latch):
            m.d.sync += reg.eq(Cat(*self.words_in))
        with m.Elif(self.shift):
            m.d.sync += reg.eq(Cat(self.word_in, reg[:-self.width]))
        return m


class ArrayDown(ArrayRegister):
    """Down- or right-shifting register."""

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        reg = Signal(self.width * self.count, reset=self.reset)
        m.d.comb += self.words_out.eq(reg)
        with m.If(self.latch):
            m.d.sync += reg.eq(self.words_in)
        with m.Elif(self.shift):
            m.d.sync += reg.eq(Cat(reg[self.width:], self.word_in))
        return m
