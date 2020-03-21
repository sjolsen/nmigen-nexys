"""Support for https://store.digilentinc.com/pmod-oled-128-x-32-pixel-monochromatic-oled-display/."""

import enum
import numbers
from typing import Optional, Tuple

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import flop
from nmigen_nexys.core import util
from nmigen_nexys.display import ssd1306
from nmigen_nexys.pmod.oled import interpreter


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

    def __init__(self, pins: Pins,
                 controller: ssd1306.SSD1306.Interface,
                 sim_logic_wait_us: Optional[numbers.Number] = None,
                 sim_vcc_wait_us: Optional[numbers.Number] = None):
        super().__init__()
        self.pins = pins
        self.controller = controller
        self.enable = Signal(reset=0)
        self.status = Signal(PowerStatus, reset=PowerStatus.OFF)
        self._sim_logic_wait_us = sim_logic_wait_us
        self._sim_vcc_wait_us = sim_vcc_wait_us

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Give control to the power-up or -down logic
        select = Signal(reset=0)
        # Explicit reset control
        m.submodules.vdd_en = vdd_en = flop.FF(1, reset=0)
        m.submodules.vbat_en = vbat_en = flop.FF(1, reset=0)
        m.submodules.reset_n = reset_n = flop.FF(1, reset=0)
        m.d.comb += self.pins.vddc.eq(~vdd_en.q)
        m.d.comb += self.pins.vbatc.eq(~vbat_en.q)
        m.d.comb += self.pins.reset.eq(reset_n.q)
        # Wall-timed state machine
        us = util.GetClockFreq(platform) // 1_000_000
        logic_delay = int((self._sim_logic_wait_us or 1000) * us)  # 1 ms
        vcc_delay = int((self._sim_vcc_wait_us or 100_000) * us)  # 100 ms
        # Use the interpreter to build the power sequence logic
        controllers = [
            ssd1306.SSD1306.Interface(self.controller.max_bits)
            for _ in range(2)
        ]
        m.d.comb += util.Multiplex(select, self.controller, controllers)
        vdd_enables = [flop.FF.Interface(1) for _ in range(2)]
        vbat_enables = [flop.FF.Interface(1) for _ in range(2)]
        m.d.comb += util.Multiplex(select, vdd_en.interface, vdd_enables)
        m.d.comb += util.Multiplex(select, vbat_en.interface, vbat_enables)
        m.submodules.power_up = power_up = interpreter.Program([
            ## Adapted from https://reference.digilentinc.com/_media/reference/pmod/pmodoled/oled.zip.
            ## See OledDriver.cpp:OledDevInit.
            # Start by turning VDD on and wait a while for the power to come up.
            interpreter.DigitalWrite(vdd_enables[0], C(1, 1)),
            interpreter.Delay(logic_delay),
            # Display off command
            interpreter.WriteCommand(ssd1306.SetDisplayOn(False)),
            # Bring Reset low and then high
            interpreter.DigitalWrite(reset_n.interface, C(0, 1)),
            interpreter.Delay(logic_delay),
            interpreter.DigitalWrite(reset_n.interface, C(1, 1)),
            # Send the Set Charge Pump and Set Pre-Charge Period commands
            interpreter.WriteCommand(ssd1306.ChargePumpSetting(True)),
            interpreter.WriteCommand(ssd1306.SetPrechargePeriod(phase1=1, phase2=15)),
            # Turn on VCC and wait 100ms
            interpreter.DigitalWrite(vbat_enables[0], C(1, 1)),
            interpreter.Delay(vcc_delay),
            # # Send the commands to invert the display.
            # interpreter.WriteCommand(ssd1306.Command(0xA1)),
            # interpreter.WriteCommand(ssd1306.Command(0xC8)),
            # # Send the commands to select sequential COM configuration
            # interpreter.WriteCommand(ssd1306.Command(0xDA)),
            # interpreter.WriteCommand(ssd1306.Command(0x20)),
            # Send Display On command
            interpreter.WriteCommand(ssd1306.SetDisplayOn(True)),
        ], controllers[0])
        m.submodules.power_down = power_down = interpreter.Program([
            ## See OledDriver.cpp:OledDevTerm.
            # Send the Display Off command.
            interpreter.WriteCommand(ssd1306.SetDisplayOn(False)),
	        # Turn off VCC
            interpreter.DigitalWrite(vbat_enables[1], C(0, 1)),
            interpreter.Delay(vcc_delay),
            # Turn off VDD
            interpreter.DigitalWrite(vdd_enables[1], C(0, 1)),
        ], controllers[1])
        m.d.sync += power_up.start.eq(0)  # default
        m.d.sync += power_down.start.eq(0)  # default
        with m.FSM(reset='OFF'):
            with m.State('OFF'):
                with m.If(self.enable):
                    m.d.sync += self.status.eq(PowerStatus.POWERING_UP)
                    m.d.sync += select.eq(0)
                    m.d.sync += power_up.start.eq(1)
                    m.next = 'POWERING_UP'
            with m.State('POWERING_UP'):
                with m.If(power_up.done):
                    m.d.sync += self.status.eq(PowerStatus.READY)
                    m.next = 'READY'
            with m.State('READY'):
                with m.If(~self.enable):
                    m.d.sync += self.status.eq(PowerStatus.POWERING_DOWN)
                    m.d.sync += select.eq(1)
                    m.d.sync += power_down.start.eq(1)
                    m.next = 'POWERING_DOWN'
            with m.State('POWERING_DOWN'):
                with m.If(power_down.done):
                    m.d.sync += self.status.eq(PowerStatus.OFF)
                    m.next = 'OFF'
        return m
