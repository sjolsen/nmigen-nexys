from nmigen_boards import nexys4ddr
from nmigen_boards.test import blinky

from nmigen_nexys.core import top


class NexysA7100TPlatform(nexys4ddr.Nexys4DDRPlatform):
    pass


if __name__ == "__main__":
    top.main(NexysA7100TPlatform(), blinky.Blinky())
