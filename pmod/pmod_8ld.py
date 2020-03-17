from nmigen import *
from nmigen.build import *

from typing import Tuple


def Pmod8LDResource(n: int, conn: Tuple[str, int]) -> Resource:
    subsignals = [
        Subsignal(
            f'ld{i}',
            Pins(str(pin), conn=conn, dir='o'),
            Attrs(IOSTANDARD="LVCMOS33"))
        for i, pin in enumerate([1, 2, 3, 4, 7, 8, 9, 10])]
    return Resource('pmod_8ld', n, *subsignals)
