"""Support for https://store.digilentinc.com/pmod-8ld-eight-high-brightness-leds/."""

from typing import Tuple

from nmigen import *
from nmigen.build import *


def Pmod8LDResource(n: int, conn: Tuple[str, int]) -> Resource:
    """Declare an LED module connected to a pmod connector."""
    subsignals = [
        Subsignal(
            f'ld{i}',
            Pins(str(pin), conn=conn, dir='o'),
            Attrs(IOSTANDARD="LVCMOS33"))
        for i, pin in enumerate([1, 2, 3, 4, 7, 8, 9, 10])]
    return Resource('pmod_8ld', n, *subsignals)
