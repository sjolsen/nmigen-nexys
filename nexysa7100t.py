from nmigen_boards.nmigen_boards.nexys4ddr import Nexys4DDRPlatform
from nmigen_boards.nmigen_boards.test.blinky import Blinky


class NexysA7100TPlatform(Nexys4DDRPlatform):
    pass


if __name__ == "__main__":
    NexysA7100TPlatform().build(Blinky(), do_program=True)