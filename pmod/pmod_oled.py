"""Support for https://store.digilentinc.com/pmod-oled-128-x-32-pixel-monochromatic-oled-display/."""

import enum
from typing import Optional, Tuple

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import shift_register
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.display import ssd1306
from nmigen_nexys.serial import spi


class PmodPins(Record):

    LAYOUT = Layout([
        ('cs', 1),
        ('mosi', 1),
        ('sclk', 1),
        ('dc', 1),
        ('reset', 1),
        ('vbatc', 1),
        ('vddc', 1),
    ])

    def __init__(self):
        super().__init__(self.LAYOUT, fields={
            name: Signal(shape, name=name)
            for name, (shape, _) in self.LAYOUT.fields.items()
        })


def PmodOLEDResource(n: int, conn: Tuple[str, int]) -> Resource:
    """Declare an OLED module connected to a pmod connector."""
    return Resource(
        'pmod_oled', n,
        Subsignal('cs', Pins('1', conn=conn, dir='o')),
        Subsignal('mosi', Pins('2', conn=conn, dir='o')),
        # Pin 3 is marked MISO, but the module isn't connected
        Subsignal('sclk', Pins('4', conn=conn, dir='o')),
        # Pin 5 is GND
        # Pin 6 is VCC
        Subsignal('dc', Pins('7', conn=conn, dir='o')),
        Subsignal('reset', Pins('8', conn=conn, dir='o')),
        Subsignal('vbatc', Pins('9', conn=conn, dir='o')),
        Subsignal('vddc', Pins('10', conn=conn, dir='o')),
        # Pin 11 is GND
        # Pin 12 is VCC
        Attrs(IOSTANDARD="LVCMOS33"))

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        return m


class PowerStatus(enum.IntEnum):
    OFF = 0
    POWERING_UP = 1
    READY = 2
    POWERING_DOWN = 3


class PowerSequencer(Elaboratable):

    _DISPLAY_ON = ssd1306.SetDisplayOn(True)
    _DISPLAY_OFF = ssd1306.SetDisplayOn(False)

    def __init__(self, pins: Pins, sim_clk_freq: Optional[int] = None,
                 sim_vcc_wait_us: Optional[int] = None):
        super().__init__()
        self.pins = pins
        self.enable = Signal(reset=0)
        self.status = Signal(PowerStatus, reset=PowerStatus.OFF)
        # TODO: This shouldn't be necessary
        self._sim_clk_freq = sim_clk_freq
        self._sim_vcc_wait_us = sim_vcc_wait_us
        self.master = spi.ShiftMaster(
            bus=spi.Bus(
                cs_n=self.pins.cs,
                clk=self.pins.sclk,
                mosi=self.pins.mosi,
                miso=Signal(name='null_miso', reset=0),
                freq_Hz=10_000_000),
            register=shift_register.Up(max(self._DISPLAY_ON.bits.width,
                                           self._DISPLAY_OFF.bits.width)),
            sim_clk_freq=self._sim_clk_freq)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Explicit reset control
        vdd_en = Signal(reset=0)
        vbat_en = Signal(reset=0)
        reset_n = Signal(reset=0)
        m.d.comb += self.pins.vddc.eq(vdd_en)
        m.d.comb += self.pins.vbatc.eq(vbat_en)
        m.d.comb += self.pins.reset.eq(reset_n)
        # Embedded SPI master for display on/off commands
        m.submodules.master = self.master
        # Wall-timed state machine
        sync_clk_freq = self._sim_clk_freq or int(platform.default_clk_frequency)
        us = sync_clk_freq // 1_000_000
        vcc_wait_us = self._sim_vcc_wait_us or 100_000  # 100 ms
        m.submodules.timer = timer = timer_module.OneShot(
            period=Signal(range(vcc_wait_us * us), reset=0))
        m.d.sync += timer.go.eq(0)  # default
        with m.FSM(reset='OFF'):
            with m.State('OFF'):
                m.d.sync += self.status.eq(PowerStatus.OFF)
                with m.If(self.enable):
                    m.d.sync += self.status.eq(PowerStatus.POWERING_UP)
                    m.d.sync += vdd_en.eq(1)
                    m.d.sync += timer.period.eq(3 * us)
                    m.d.sync += timer.go.eq(1)
                    m.next = 'HOLDING_RESET'
            with m.State('HOLDING_RESET'):
                with m.If(timer.triggered):
                    m.d.sync += reset_n.eq(1)
                    m.d.sync += vbat_en.eq(1)
                    m.d.sync += timer.period.eq(1 * us)
                    m.d.sync += timer.go.eq(1)
                    m.next = 'WAITING_FOR_VCC_READY'
            with m.State('WAITING_FOR_VCC_READY'):
                with m.If(timer.triggered):
                    self.WriteCommand(m, self._DISPLAY_ON)
                    m.next = 'WAITING_FOR_DISPLAY_ON'
            with m.State('WAITING_FOR_DISPLAY_ON'):
                with m.If(self.WaitDone(m)):
                    m.d.sync += timer.period.eq(vcc_wait_us * us)
                    m.d.sync += timer.go.eq(1)
                    m.next = 'WAITING_FOR_SEG_COM_ON'
            with m.State('WAITING_FOR_SEG_COM_ON'):
                with m.If(timer.triggered):
                    m.d.sync += self.status.eq(PowerStatus.READY)
                    m.next = 'ON'
            with m.State('ON'):
                with m.If(~self.enable):
                    m.d.sync += self.status.eq(PowerStatus.POWERING_DOWN)
                    self.WriteCommand(m, self._DISPLAY_OFF)
                    m.next = 'WAITING_FOR_DISPLAY_OFF'
            with m.State('WAITING_FOR_DISPLAY_OFF'):
                with m.If(self.WaitDone(m)):
                    m.d.sync += vbat_en.eq(0)
                    m.d.sync += timer.period.eq(vcc_wait_us * us)
                    m.d.sync += timer.go.eq(1)
                    m.next = 'WAITING_FOR_VCC_OFF'
            with m.State('WAITING_FOR_VCC_OFF'):
                with m.If(timer.triggered):
                    m.d.sync += vdd_en.eq(0)
                    m.next = 'OFF'
        return m

    def WriteCommand(self, m: Module, command: ssd1306.Command):
        m.d.sync += self.pins.dc.eq(0)
        padding_bits = self.master.register.width - command.bits.width
        m.d.sync += self.master.register.word_in.eq(
            Cat(C(0, padding_bits), command.bits))
        m.d.sync += self.master.register.latch.eq(1)
        m.d.sync += self.master.start.eq(1)

    def WaitDone(self, m: Module) -> Value:
        m.d.sync += self.master.register.latch.eq(0)
        m.d.sync += self.master.start.eq(0)
        return self.master.done
