from nmigen_boards import nexys4ddr
from nmigen_boards.test import blinky


class NexysA7100TPlatform(nexys4ddr.Nexys4DDRPlatform):
    pass


if __name__ == "__main__":
    NexysA7100TPlatform().build(blinky.Blinky(), do_program=True)
