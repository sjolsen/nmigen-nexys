from nmigen_boards.nexys4ddr import *
from nmigen_boards.test.blinky import *


class NexysA7100TPlatform(Nexys4DDRPlatform):
    pass


if __name__ == "__main__":
    NexysA7100TPlatform().build(Blinky(), do_program=True)