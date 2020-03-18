"""nMigen support for https://store.digilentinc.com/nexys-a7-fpga-trainer-board-recommended-for-ece-curriculum/."""

from nmigen_boards import nexys4ddr
from nmigen_boards.test import blinky

from nmigen_nexys.core import top


class NexysA7100TPlatform(nexys4ddr.Nexys4DDRPlatform):
    """Platform for the Digilent Nexys A7-100T.
    
    This board is functionally identical to the discontinued Nexys 4 DDR.
    """


if __name__ == "__main__":
    top.main(NexysA7100TPlatform(), blinky.Blinky())
