"""Driver for the SSD1306 128x64 dot matrix display driver.

Datasheet: https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf.
"""

import enum
from typing import Any, Literal, NamedTuple

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *


class Command(NamedTuple):
    """Encoded display controller command."""
    data: bytes

    def __init__(self, *ints):
        super().__init__(data=bytes(ints))


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


def SetContrast(contrast: int) -> Command:
    """Set Contrast Control.

    Double byte command to select 1 out of 256 contrast steps. Contrast
    increases as the value increases.  (RESET = 7Fh)
    """
    return Command(0x81, contrast)


def EntireDisplayOn(override_ram: bool) -> Command:
    """Entire Display ON.

    Args:
        override_ram:
            False: Resume to RAM content display (RESET). Output follows RAM
                   content.
            True: Entire display ON. Output ignores RAM content.
    """
    return Command(0xA4 | int(override_ram))


def SetInverseDisplay(invert: bool) -> Command:
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
    return Command(0xA6 | int(invert))


def SetDisplayOn(on: bool) -> Command:
    """Set Display ON/OFF.

    Args:
        on:
            False: Display OFF (sleep mode) (RESET)
            True: Display ON in normal mode
    """
    return Command(0xAE | int(on))


# 2. Scrolling commands


def ContinuousHorizontalScrollSetup(
        direction: Literal['right', 'left'],
        start_page: int,
        frame_interval: Literal[2, 3, 4, 5, 25, 64, 128, 256],
        end_page: int) -> Command:
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
    return Command(code, A, B, C, D, E, F)


# TODO: Remaining scrolling commands


# 3. Addressing setting commands


def SetLowerColumnStartAddress(address: int) -> Command:
    """Set Lower Column Start Address for Page Addressing Mode.

    Set the lower nibble of the column start address register for Page
    Addressing Mode using address as data bits. The initial display line
    register is reset to 0000b after RESET.

    Note: This command is only for page addressing mode.
    """
    if not 0 <= address < 16:
        raise CommandEncodingError('SetLowerColumnStartAddress', 'address',
                                   address)
    return Command(address)


def SetHigherColumnStartAddress(address: int) -> Command:
    """Set Higher Column Start Address for Page Addressing Mode.

    Set the higher nibble of the column start address register for Page
    Addressing Mode using address as data bits. The initial display line
    register is reset to 0000b after RESET.

    Note: This command is only for page addressing mode.
    """
    if not 0 <= address < 16:
        raise CommandEncodingError('SetLowerColumnStartAddress', 'address',
                                   address)
    return Command(0x10 | address)


class AddressingMode(enum.IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1
    PAGE = 2


def SetMemoryAddressingMode(mode: AddressingMode) -> Command:
    """Set Memory Addressing Mode.

    Args:
        mode:
            HORIZONTAL: Horizontal Addressing Mode
            VERTICAL: Vertical Addressing Mode
            PAGE: Page Addressing Mode
    """
    return Command(0x20, int(mode))


def SetColumnAddress(start_address: int, end_address: int) -> Command:
    """Set Column Address.

    Setup column start and end address.

    Note: This command is only for horizontal or vertical addressing mode. 

    Args:
        start_address: Column start address
            Range: 0-127 (RESET = 0)
        end_address: Column end address
            Range: 0-127 (RESET = 127)
    """
    if not 0 <= start_address < 128:
        raise CommandEncodingError('SetColumnAddress', 'start_address',
                                   start_address)
    if not 0 <= end_address < 128:
        raise CommandEncodingError('SetColumnAddress', 'end_address',
                                   end_address)
    return Command(0x21, start_address, end_address)


def SetPageAddress(start_address: int, end_address: int) -> Command:
    """Set Page Address.

    Setup page start and end address.

    Note: This command is only for horizontal or vertical addressing mode. 

    Args:
        start_address: Page start Address
            Range: 0-7 (RESET = 0)
        end_address: Page end Address
            Range: 0-7 (RESET = 7)
    """
    if not 0 <= start_address < 8:
        raise CommandEncodingError('SetPageAddress', 'start_address',
                                   start_address)
    if not 0 <= end_address < 8:
        raise CommandEncodingError(
            'SetPageAddress', 'end_address', end_address)
    return Command(0x22, start_address, end_address)


def SetPageStartAddress(page: int) -> Command:
    """Set Page Start Address for Page Addressing Mode.

    Set GDDRAM Page Start Address (PAGE0~PAGE7) for Page Addressing Mode using
    page.

    Note: This command is only for page addressing mode.
    """
    if not 0 <= page < 8:
        raise CommandEncodingError('SetPageStartAddress', 'page', page)
    return Command(0xB0 | page)


# 4. Hardware configuration (panel resolution & layout related) commands


def SetDisplayStartLine(start_line: int) -> Command:
    """Set Display Start Line.

    Set display RAM display start line register from 0-63. Display start line
    register is reset to 000000b during RESET.
    """
    if not 0 <= start_line < 64:
        raise CommandEncodingError('SetDisplayStartLine', 'start_line',
                                   start_line)
    return Command(0x40 | start_line)


def SetSegmentRemap(reverse: bool) -> Command:
    """"Set Segment Re-map.

    Args:
        reverse:
            False: Column address 0 is mapped to SEG0 (RESET)
            True: Column address 127 is mapped to SEG0
    """
    return Command(0xA0 | int(reverse))


def SetMultiplexRatio(ratio: int) -> Command:
    """Set Multiplex Ratio.

    Args:
        ratio: The multiplex ratio. This function automatically handles the
               N - 1 encoding.
            Range: 16 to 64, RESET = 64
    """
    if not 16 <= ratio <= 64:
        raise CommandEncodingError('SetMultiplexRatio', 'ratio', ratio)
    return Command(0xA8, ratio - 1)


# TODO: Remaining configuration commands


# 5. Timing and driving scheme setting commands
# TODO


class SPI4WireInterface(Record):

    LAYOUT = Layout([
        ('cs_n', 1),
        ('dc', 1),
        ('sclk', 1),
        ('sdin', 1),
    ])

    def __init__(self, cs_n: Signal, dc: Signal, sclk: Signal, sdin: Signal):
        super().__init__(self.LAYOUT,
                         fields={f: locals()[f] for f in self.LAYOUT})
