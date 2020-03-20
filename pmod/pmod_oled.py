"""Support for https://store.digilentinc.com/pmod-oled-128-x-32-pixel-monochromatic-oled-display/."""

import enum
from typing import Optional, Tuple

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import shift_register
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import util
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

    def ControllerBus(self) -> ssd1306.Bus:
        return ssd1306.Bus(
            reset_n=self.reset,
            dc=self.dc,
            cs_n=self.cs,
            clk=self.sclk,
            mosi=self.mosi)


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


class PowerStatus(enum.IntEnum):
    OFF = 0
    POWERING_UP = 1
    READY = 2
    POWERING_DOWN = 3


class PowerSequencer(Elaboratable):

    _CHARGE_PUMP_ON = ssd1306.ChargePumpSetting(True)
    _DISPLAY_ON = ssd1306.SetDisplayOn(True)
    _DISPLAY_OFF = ssd1306.SetDisplayOn(False)
    _CHARGE_PUMP_OFF = ssd1306.ChargePumpSetting(False)

    def __init__(self, pins: Pins,
                 controller: ssd1306.SSD1306.Interface,
                 sim_vcc_wait_us: Optional[int] = None):
        super().__init__()
        self.pins = pins
        self.controller = controller
        self.enable = Signal(reset=0)
        self.status = Signal(PowerStatus, reset=PowerStatus.OFF)
        self._sim_vcc_wait_us = sim_vcc_wait_us

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Explicit reset control
        vdd_en = Signal(reset=0)
        vbat_en = Signal(reset=0)
        reset_n = Signal(reset=0)
        m.d.comb += self.pins.vddc.eq(~vdd_en)
        m.d.comb += self.pins.vbatc.eq(~vbat_en)
        m.d.comb += self.controller.reset_n.eq(reset_n)
        # Wall-timed state machine
        us = util.GetClockFreq(platform) // 1_000_000
        vcc_wait_us = self._sim_vcc_wait_us or 100_000  # 100 ms
        m.submodules.timer = timer = timer_module.OneShot(
            period=Signal(range(vcc_wait_us * us), reset=0))
        m.d.sync += timer.go.eq(0)  # default
        m.d.sync += self.controller.start.eq(0)  # default
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
                    m.d.sync += self.controller.WriteCommand(
                        self._CHARGE_PUMP_ON)
                    m.d.sync += self.controller.start.eq(1)
                    m.next = 'WAITING_FOR_CHARGE_PUMP_ON'
            with m.State('WAITING_FOR_CHARGE_PUMP_ON'):
                with m.If(self.controller.done):
                    m.d.sync += vbat_en.eq(1)
                    m.d.sync += timer.period.eq(vcc_wait_us * us)
                    m.d.sync += timer.go.eq(1)
                    m.next = 'WAITING_FOR_VCC_ON'
            with m.State('WAITING_FOR_VCC_ON'):
                with m.If(timer.triggered):
                    m.d.sync += self.controller.WriteCommand(
                        self._DISPLAY_ON)
                    m.d.sync += self.controller.start.eq(1)
                    m.next = 'WAITING_FOR_DISPLAY_ON'
            with m.State('WAITING_FOR_DISPLAY_ON'):
                with m.If(self.controller.done):
                    m.d.sync += self.status.eq(PowerStatus.READY)
                    m.next = 'ON'
            with m.State('ON'):
                with m.If(~self.enable):
                    m.d.sync += self.status.eq(PowerStatus.POWERING_DOWN)
                    m.d.sync += self.controller.WriteCommand(
                        self._DISPLAY_OFF)
                    m.d.sync += self.controller.start.eq(1)
                    m.next = 'WAITING_FOR_DISPLAY_OFF'
            with m.State('WAITING_FOR_DISPLAY_OFF'):
                with m.If(self.controller.done):
                    m.d.sync += self.controller.WriteCommand(
                        self._CHARGE_PUMP_OFF)
                    m.d.sync += self.controller.start.eq(1)
                    m.next = 'WAITING_FOR_CHARGE_PUMP_OFF'
            with m.State('WAITING_FOR_CHARGE_PUMP_OFF'):
                with m.If(self.controller.done):
                    m.d.sync += vbat_en.eq(0)
                    m.d.sync += timer.period.eq(vcc_wait_us * us)
                    m.d.sync += timer.go.eq(1)
                    m.next = 'WAITING_FOR_VCC_OFF'
            with m.State('WAITING_FOR_VCC_OFF'):
                with m.If(timer.triggered):
                    m.d.sync += vdd_en.eq(0)
                    m.next = 'OFF'
        return m
