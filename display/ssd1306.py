"""Driver for the SSD1306 128x64 dot matrix display driver.

Datasheet: https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf.
"""

import enum
from typing import Any, Iterable, Literal, Union

from nmigen import *
from nmigen.build import *
from nmigen.hdl.ast import Assign
from nmigen.hdl.rec import Direction, Layout, Record

from nmigen_nexys.core import shift_register
from nmigen_nexys.core import util
from nmigen_nexys.serial import spi


MAX_COMMAND_BYTES = 7


class Command(object):
    """Encoded display controller command."""

    def __init__(self, *ints):
        super().__init__()
        assert len(ints) <= MAX_COMMAND_BYTES
        self.data = bytes(ints)

    def __repr__(self) -> str:
        if type(self) is Command:
            ints = [f'0x{b:02X}' for b in self.data]
            return f'Command({", ".join(ints)})'
        return util.ProductRepr(self)

    @property
    def bits(self) -> Const:
        return C(
            int.from_bytes(self.data, byteorder='big'),
            8 * len(self.data))


class CommandEncodingError(Exception):
    """Error encountered during command encoding."""

    def __init__(self, command: str, parameter: str, value: Any):
        super().__init__()
        self.command = command
        self.parameter = parameter
        self.value = value

    def __str__(self):
        return (
            f'Could not encode command {self.command} with parameter '
            f'{self.parameter}={self.value}')


# 1. Fundamental commands


class SetContrast(Command):
    """Set Contrast Control.

    Double byte command to select 1 out of 256 contrast steps. Contrast
    increases as the value increases.  (RESET = 7Fh)
    """

    def __init__(self, contrast: int):
        super().__init__(0x81, contrast)
        self.contrast = contrast


class EntireDisplayOn(Command):
    """Entire Display ON.

    Args:
        override_ram:
            False: Resume to RAM content display (RESET). Output follows RAM
                   content.
            True: Entire display ON. Output ignores RAM content.
    """

    def __init__(self, override_ram: bool):
        super().__init__(0xA4 | int(override_ram))
        self.override_ram = override_ram


class SetInverseDisplay(Command):
    """Set Normal/Inverse Display.

    Args:
        invert:
            False: Normal display (RESET)
                0 in RAM: OFF in display panel
                1 in RAM: ON in display panel
            True: Inverse display
                0 in RAM: ON in display panel
                1 in RAM: OFF in display panel
    """

    def __init__(self, invert: bool):
        super().__init__(0xA6 | int(invert))
        self.invert = invert


class SetDisplayOn(Command):
    """Set Display ON/OFF.

    Args:
        on:
            False: Display OFF (sleep mode) (RESET)
            True: Display ON in normal mode
    """

    def __init__(self, on: bool):
        super().__init__(0xAE | int(on))
        self.on = on


# 2. Scrolling commands


class ContinuousHorizontalScrollSetup(Command):
    """Continuous Horizontal Scroll Setup.

    Args:
        direction: Horizontal scroll by 1 column
            'right': Right Horizontal Scroll
            'left': Left Horizontal Scroll
        start_page: Define start page address
            0: PAGE0
            ...
            7: PAGE7
        frame_interval: Set time interval between each scroll step in
                        terms of frame frequency
            Legal values are 2, 3, 4, 5, 25, 64, 128, or 256.
        end_page: Define end page address. The value of end_page must be larger
                  or equal to start_page.
            0: PAGE0
            ...
            7: PAGE7
    """

    def __init__(
            self,
            direction: Literal['right', 'left'],
            start_page: int,
            frame_interval: Literal[2, 3, 4, 5, 25, 64, 128, 256],
            end_page: int):
        direction_codes = {'right': 0, 'left': 1}
        if direction not in direction_codes:
            raise CommandEncodingError('ContinuousHorizontalScrollSetup',
                                       'direction', direction)
        code = direction_codes[direction]
        A = 0x00
        if not 0 <= start_page <= 7:
            raise CommandEncodingError('ContinuousHorizontalScrollSetup',
                                       'start_page', start_page)
        B = start_page
        interval_codes = {5: 0, 64: 1, 128: 2, 256: 3, 3: 4, 4: 5, 25: 6, 2: 7}
        if frame_interval not in interval_codes:
            raise CommandEncodingError('ContinuousHorizontalScrollSetup',
                                       'frame_interval', frame_interval)
        C = interval_codes[frame_interval]
        if not start_page <= end_page <= 7:
            raise CommandEncodingError('ContinuousHorizontalScrollSetup',
                                       'end_page', end_page)
        D = end_page
        E = 0x00
        F = 0xFF
        super().__init__(code, A, B, C, D, E, F)
        self.direction = direction
        self.start_page = start_page
        self.frame_interval = frame_interval
        self.end_page = end_page


# TODO: Remaining scrolling commands


# 3. Addressing setting commands


# def SetLowerColumnStartAddress(address: int) -> Command:
#     """Set Lower Column Start Address for Page Addressing Mode.

#     Set the lower nibble of the column start address register for Page
#     Addressing Mode using address as data bits. The initial display line
#     register is reset to 0000b after RESET.

#     Note: This command is only for page addressing mode.
#     """
#     if not 0 <= address < 16:
#         raise CommandEncodingError('SetLowerColumnStartAddress', 'address',
#                                    address)
#     return Command(address)


# def SetHigherColumnStartAddress(address: int) -> Command:
#     """Set Higher Column Start Address for Page Addressing Mode.

#     Set the higher nibble of the column start address register for Page
#     Addressing Mode using address as data bits. The initial display line
#     register is reset to 0000b after RESET.

#     Note: This command is only for page addressing mode.
#     """
#     if not 0 <= address < 16:
#         raise CommandEncodingError('SetLowerColumnStartAddress', 'address',
#                                    address)
#     return Command(0x10 | address)


class AddressingMode(enum.IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1
    PAGE = 2


class SetMemoryAddressingMode(Command):
    """Set Memory Addressing Mode.

    Args:
        mode:
            HORIZONTAL: Horizontal Addressing Mode
            VERTICAL: Vertical Addressing Mode
            PAGE: Page Addressing Mode
    """

    def __init__(self, mode: AddressingMode):
        super().__init__(0x20, int(mode))
        self.mode = mode


# def SetColumnAddress(start_address: int, end_address: int) -> Command:
#     """Set Column Address.

#     Setup column start and end address.

#     Note: This command is only for horizontal or vertical addressing mode. 

#     Args:
#         start_address: Column start address
#             Range: 0-127 (RESET = 0)
#         end_address: Column end address
#             Range: 0-127 (RESET = 127)
#     """
#     if not 0 <= start_address < 128:
#         raise CommandEncodingError('SetColumnAddress', 'start_address',
#                                    start_address)
#     if not 0 <= end_address < 128:
#         raise CommandEncodingError('SetColumnAddress', 'end_address',
#                                    end_address)
#     return Command(0x21, start_address, end_address)


# def SetPageAddress(start_address: int, end_address: int) -> Command:
#     """Set Page Address.

#     Setup page start and end address.

#     Note: This command is only for horizontal or vertical addressing mode. 

#     Args:
#         start_address: Page start Address
#             Range: 0-7 (RESET = 0)
#         end_address: Page end Address
#             Range: 0-7 (RESET = 7)
#     """
#     if not 0 <= start_address < 8:
#         raise CommandEncodingError('SetPageAddress', 'start_address',
#                                    start_address)
#     if not 0 <= end_address < 8:
#         raise CommandEncodingError(
#             'SetPageAddress', 'end_address', end_address)
#     return Command(0x22, start_address, end_address)


# def SetPageStartAddress(page: int) -> Command:
#     """Set Page Start Address for Page Addressing Mode.

#     Set GDDRAM Page Start Address (PAGE0~PAGE7) for Page Addressing Mode using
#     page.

#     Note: This command is only for page addressing mode.
#     """
#     if not 0 <= page < 8:
#         raise CommandEncodingError('SetPageStartAddress', 'page', page)
#     return Command(0xB0 | page)


# 4. Hardware configuration (panel resolution & layout related) commands


# def SetDisplayStartLine(start_line: int) -> Command:
#     """Set Display Start Line.

#     Set display RAM display start line register from 0-63. Display start line
#     register is reset to 000000b during RESET.
#     """
#     if not 0 <= start_line < 64:
#         raise CommandEncodingError('SetDisplayStartLine', 'start_line',
#                                    start_line)
#     return Command(0x40 | start_line)


# def SetSegmentRemap(reverse: bool) -> Command:
#     """"Set Segment Re-map.

#     Args:
#         reverse:
#             False: Column address 0 is mapped to SEG0 (RESET)
#             True: Column address 127 is mapped to SEG0
#     """
#     return Command(0xA0 | int(reverse))


# def SetMultiplexRatio(ratio: int) -> Command:
#     """Set Multiplex Ratio.

#     Args:
#         ratio: The multiplex ratio. This function automatically handles the
#                N - 1 encoding.
#             Range: 16 to 64, RESET = 64
#     """
#     if not 16 <= ratio <= 64:
#         raise CommandEncodingError('SetMultiplexRatio', 'ratio', ratio)
#     return Command(0xA8, ratio - 1)


# TODO: Remaining configuration commands


# 5. Timing and driving scheme setting commands
# TODO


class SetPrechargePeriod(Command):
    """Set Pre-charge Period.

    Args:
        phase1: Phase 1 period of up to 15 DCLK clocks
            0 is invalid entry (RESET=2h)
        phase2: Phase 2 period of up to 15 DCLK clocks
            0 is invalid entry (RESET=2h)
    """

    def __init__(self, phase1: int, phase2: int):
        assert 0 < phase1 < 16
        assert 0 < phase2 < 16
        super().__init__(0xD9, phase1 | (phase2 << 4))
        self.phase1 = phase1
        self.phase2 = phase2


class ChargePumpSetting(Command):
    """Charge Pump Setting.

    Note: The Charge Pump must be enabled by the following command:
        8Dh ; Charge Pump Setting
        14h ; Enable Charge Pump
        AFh ; Display ON

    Args:
        enable:
            False: Disable charge pump (RESET)
            True: Enable charge pump during display on
    """

    def __init__(self, enable: bool):
        super().__init__(0x8D, 0x10 | (int(enable) << 2))
        self.enable = enable


class Bus(Record):
    """Write-only SPI bus + data/command control line."""

    LAYOUT = Layout([
        ('dc', 1, Direction.FANOUT),
        ('cs_n', 1, Direction.FANOUT),
        ('clk', 1, Direction.FANOUT),
        ('mosi', 1, Direction.FANOUT),
    ])

    def __init__(self, **kwargs):
        super().__init__(self.LAYOUT, fields=kwargs)

    def SPIBus(self) -> spi.Bus:
        """Convert to a 10 MHz SPI bus handle."""
        return spi.Bus(
            cs_n=self.cs_n,
            clk=self.clk,
            mosi=self.mosi,
            miso=Signal(name='miso', reset=0),
            freq_Hz=10_000_000)


class Controller(Elaboratable):
    """SPI master controller for the SSD1306."""

    class Interface(Record):
        """Muxable interface for nmigen_nexys.display.ssd1306.Controller."""

        def __init__(self, max_bits: int):
            super().__init__(Layout([
                ('dc', 1, Direction.FANIN),
                ('data', max_bits, Direction.FANIN),
                ('data_size', range(max_bits + 1), Direction.FANIN),
                ('start', 1, Direction.FANIN),
                ('done', 1, Direction.FANOUT),
            ]))
            self.max_bits = max_bits

        def WriteData(self, data: Union[bytes, Signal], dc=1) -> Iterable[Assign]:
            """Sync macro to stage data for transfer."""
            if isinstance(data, bytes):
                data_size = 8 * len(data)
                assert 0 < data_size <= self.data.width
                bits = int.from_bytes(data, byteorder='big')
            elif isinstance(data, Signal):
                data_size = data.width
                bits = data
            yield self.dc.eq(dc)
            yield self.data[-data_size:].eq(bits)
            yield self.data_size.eq(data_size)

        def WriteCommand(self, command: Command) -> Iterable[Assign]:
            """Sync macro to stage a command for transfer."""
            yield from self.WriteData(command.data, dc=0)

    def __init__(self, bus: Bus, max_data_bytes: int):
        super().__init__()
        self.bus = bus
        self.max_bits = 8 * max(max_data_bytes, MAX_COMMAND_BYTES)
        self.interface = self.Interface(self.max_bits)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.d.comb += self.bus.dc.eq(self.interface.dc)
        m.submodules.master = master = spi.ShiftMaster(
            self.bus.SPIBus(), shift_register.Up(self.max_bits))
        m.d.comb += master.interface.mosi_data.eq(self.interface.data)
        m.d.comb += master.interface.transfer_size.eq(self.interface.data_size)
        m.d.comb += master.interface.start.eq(self.interface.start)
        m.d.comb += self.interface.done.eq(master.interface.done)
        return m
