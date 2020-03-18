import abc

from nmigen import *
from nmigen.build import *


class Register(Elaboratable):

    def __init__(self, width: int):
        super().__init__()
        self.width = width
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

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        reg = Signal(self.width)
        m.d.comb += self.word_out.eq(reg)
        m.d.comb += self.bit_out.eq(reg[-1])
        with m.If(self.latch):
            m.d.sync += reg.eq(self.word_in)
        with m.Elif(self.shift):
            m.d.sync += reg.eq(Cat(self.bit_in, reg[:-1]))
        return m


class Down(Register):

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        reg = Signal(self.width)
        m.d.comb += self.word_out.eq(reg)
        m.d.comb += self.bit_out.eq(reg[0])
        with m.If(self.latch):
            m.d.sync += reg.eq(self.word_in)
        with m.Elif(self.shift):
            m.d.sync += reg.eq(Cat(reg[1:], self.bit_in))
        return m
