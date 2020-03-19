"""Implementation of https://en.wikipedia.org/wiki/Serial_Peripheral_Interface.

This module provides elaboratables for generating and decoding bus events. It
also defines a SPI slave and master based on shift registers. These
implementations are provided as a reference for integrating ClockEngine and
BusDecoder moreso than as functional endpoints. This module does not implement
multiplexing of chip select or tri-stating of MISO.
"""

import enum
from typing import Optional

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import edge
from nmigen_nexys.core import shift_register
from nmigen_nexys.core import timer
from nmigen_nexys.core import util


class Bus(Record):
    """Single-lane bidirectional SPI bus with chip select."""

    LAYOUT = Layout([
        ('cs_n', 1),
        ('clk', 1),
        ('mosi', 1),
        ('miso', 1),
    ])

    def __init__(
            self, cs_n: Signal, clk: Signal, mosi: Signal, miso: Signal,
            freq_Hz: int):
        super().__init__(self.LAYOUT, fields={
            'cs_n': cs_n,
            'clk': clk,
            'mosi': mosi,
            'miso': miso,
        })
        self.freq_Hz = freq_Hz


class ClockEngine(Elaboratable):
    """Bus clock and chip select frame generator.

    When enable is asserted, the clock source will pull chip select low and
    begin generating clocks. When enable is released, the clock source will
    finish the current clock cycle and drive chip select high. The enable
    signal should not be asserted again until chip select is deasserted.

    The polarity signal determines whether the clock is held high or low during
    idle. With polarity 0, the clock is low during idle and a clock cycle begins
    with the rising edge and ends with the falling edge. With polarity 1, the
    clock is high during idle and a clock cycle begins with the falling edge and
    ends with the rising edge.
    """

    def __init__(self, bus: Bus, polarity: Signal,
                 sim_clk_freq: Optional[int] = None):
        super().__init__()
        self.bus = bus
        self.polarity = polarity
        self.enable = Signal(reset=0)
        # TODO: This shouldn't be necessary
        self._sim_clk_freq = sim_clk_freq

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Use local signals to give us control over register reset values
        assert_cs = Signal(reset=0)
        assert_clk = Signal(reset=0)
        m.d.comb += self.bus.cs_n.eq(~assert_cs)
        m.d.comb += self.bus.clk.eq(assert_clk ^ self.polarity)
        # Set up a timer to start when enable is asserted and run at twice the
        # bus frequency until the transaction ends
        m.submodules.en_edge = en_edge = edge.Detector(self.enable)
        sync_clk_freq = self._sim_clk_freq or int(platform.default_clk_frequency)
        m.submodules.hclk_timer = hclk_timer = timer.OneShot(
            sync_clk_freq // (2 * self.bus.freq_Hz))
        m.d.comb += hclk_timer.go.eq(
            en_edge.rose | (assert_cs & hclk_timer.triggered))
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(en_edge.rose):
                    m.d.sync += assert_cs.eq(1)
                    m.next = 'LEADING_EDGE'
            with m.State('LEADING_EDGE'):
                with m.If(hclk_timer.triggered):
                    with m.If(~self.enable):
                        # End of transaction
                        m.d.sync += assert_cs.eq(0)
                        m.next = 'IDLE'
                    with m.Else():
                        m.d.sync += assert_clk.eq(1)
                        m.next = 'TRAILING_EDGE'
            with m.State('TRAILING_EDGE'):
                with m.If(hclk_timer.triggered):
                    m.d.sync += assert_clk.eq(0)
                    m.next = 'LEADING_EDGE'
        return m


class BusEvent(enum.IntEnum):
    """Bus event decoded by spi.BusDecoder."""
    START = 0
    SETUP = 1
    SAMPLE = 2
    STOP = 3


class BusDecoder(Elaboratable):
    """Listen to the bus for (potentially simultaneous) events.

    BusDecoder exposes bus events via the events bitmask. The START event
    corresponds to chip select assertion; likewise, the STOP event corresponds
    to chip select deassertion. On the SETUP event, the bus endpoint should make
    its output available and hold until the next SETUP or STOP event. On SAMPLE,
    the endpoint should sample its input.

    Events are only emitted if chip select is asserted, making this decoder
    suitable for use in slaves on multi-drop buses.
    """

    def __init__(self, bus: Bus, polarity: Signal, phase: Signal):
        super().__init__()
        self.bus = bus
        self.polarity = polarity
        self.phase = phase
        self.events = Signal(4, reset=0)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.submodules.cs_edge = cs_edge = edge.Detector(self.bus.cs_n)
        m.submodules.clk_edge = clk_edge = edge.Detector(self.bus.clk)
        m.d.comb += self.events[BusEvent.START].eq(cs_edge.fell)
        m.d.comb += self.events[BusEvent.STOP].eq(cs_edge.rose)
        leading_edge = Signal()
        trailing_edge = Signal()
        with m.Switch(self.polarity):
            with m.Case(0):
                m.d.comb += leading_edge.eq(clk_edge.rose)
                m.d.comb += trailing_edge.eq(clk_edge.fell)
                m.d.comb += self.events[BusEvent.SETUP].eq(
                    cs_edge.fell | trailing_edge)
                m.d.comb += self.events[BusEvent.SAMPLE].eq(leading_edge)
            with m.Case(1):
                m.d.comb += leading_edge.eq(clk_edge.fell)
                m.d.comb += trailing_edge.eq(clk_edge.rose)
                m.d.comb += self.events[BusEvent.SETUP].eq(leading_edge)
                m.d.comb += self.events[BusEvent.SAMPLE].eq(trailing_edge)
        # Do not emit SETUP/SAMPLE events if we're not being addressed
        with m.If(self.bus.cs_n):
            m.d.comb += self.events[BusEvent.SETUP].eq(0)
            m.d.comb += self.events[BusEvent.SAMPLE].eq(0)
        return m


class ShiftMaster(Elaboratable):
    """Reference implementation of a SPI master based on a shift register."""

    def __init__(self, bus: Bus, register: shift_register.Register,
                 sim_clk_freq: Optional[int] = None):
        super().__init__()
        self.bus = bus
        self.register = register
        self.polarity = Signal(reset=0)
        self.phase = Signal(reset=0)
        self.transfer_size = Signal(range(register.width + 1), reset=0)
        self.start = Signal(reset=0)
        self.busy = Signal(reset=0)
        self.done = Signal(reset=0)
        # TODO: This shouldn't be necessary
        self._sim_clk_freq = sim_clk_freq

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.submodules.register = self.register
        m.submodules.clk_eng = clk_eng = ClockEngine(self.bus, self.polarity,
                                                     self._sim_clk_freq)
        m.submodules.decoder = decoder = BusDecoder(
            self.bus, self.polarity, self.phase)
        remaining = Signal(self.transfer_size.width)
        m.d.comb += self.register.bit_in.eq(self.bus.miso)
        m.d.sync += self.register.shift.eq(0)  # default
        m.d.sync += self.done.eq(0)  # default
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += remaining.eq(self.transfer_size)
                    m.d.sync += self.busy.eq(1)
                    m.d.sync += clk_eng.enable.eq(1)
                    m.next = 'EVENT_LOOP'
            with m.State('EVENT_LOOP'):
                with m.If(decoder.events[BusEvent.SETUP]):
                    m.d.sync += self.bus.mosi.eq(self.register.bit_out)
                with m.If(decoder.events[BusEvent.SAMPLE]):
                    m.d.sync += self.register.shift.eq(1)
                    with m.If(remaining == 1):
                        m.d.sync += clk_eng.enable.eq(0)
                    m.d.sync += remaining.eq(remaining - 1)
                with m.If(decoder.events[BusEvent.STOP]):
                    m.d.sync += self.busy.eq(0)
                    m.d.sync += self.done.eq(self.busy)
                    m.next = 'IDLE'
        return m


class ShiftSlave(Elaboratable):
    """Reference implementation of a SPI slave based on a shift register."""

    def __init__(self, bus: Bus, register: shift_register.Register):
        super().__init__()
        self.bus = bus
        self.register = register
        self.polarity = Signal(reset=0)
        self.phase = Signal(reset=0)
        self.transfer_size = Signal(range(register.width + 1), reset=0)
        self.overrun = Signal(reset=0)
        self.start = Signal(reset=0)
        self.busy = Signal(reset=0)
        self.done = Signal(reset=0)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.submodules.register = self.register
        m.submodules.decoder = decoder = BusDecoder(
            self.bus, self.polarity, self.phase)
        m.d.comb += self.register.bit_in.eq(self.bus.mosi)
        m.d.sync += self.register.shift.eq(0)  # default
        m.d.sync += self.start.eq(0)  # default
        m.d.sync += self.done.eq(0)  # default
        with m.If(decoder.events[BusEvent.START]):
            m.d.sync += self.transfer_size.eq(0)
            m.d.sync += self.overrun.eq(0)
            m.d.sync += self.start.eq(1)
            m.d.sync += self.busy.eq(1)
        with m.If(decoder.events[BusEvent.SETUP]):
            m.d.sync += self.bus.miso.eq(self.register.bit_out)
        with m.If(decoder.events[BusEvent.SAMPLE]):
            m.d.sync += self.register.shift.eq(1)
            with m.If(self.transfer_size == self.register.width):
                m.d.sync += self.overrun.eq(1)
            m.d.sync += self.transfer_size.eq(
                util.SatAdd(self.transfer_size, 1, limit=self.register.width))
        with m.If(decoder.events[BusEvent.STOP]):
            m.d.sync += self.busy.eq(0)
            m.d.sync += self.done.eq(self.busy)
        return m
