"""nMigen support for https://store.digilentinc.com/nexys-a7-fpga-trainer-board-recommended-for-ece-curriculum/."""

from absl import app
from nmigen.build import *
from nmigen_boards import nexys4ddr
from nmigen_boards.test import blinky

from nmigen_nexys.bazel import top


def JTAGResource(*args, tck, tdi, tdo, tms, conn=None, attrs=None):
    io = [
        Subsignal("tck", Pins(tck, dir="i", conn=conn, assert_width=1)),
        Subsignal("tdi", Pins(tdi, dir="i", conn=conn, assert_width=1)),
        Subsignal("tdo", Pins(tdo, dir="i", conn=conn, assert_width=1)),
        Subsignal("tms", Pins(tms, dir="i", conn=conn, assert_width=1)),
    ]
    if attrs is not None:
        io.append(attrs)
    return Resource.family(*args, default_name="jtag", ios=io)


class NexysA7100TPlatform(nexys4ddr.Nexys4DDRPlatform):
    """Platform for the Digilent Nexys A7-100T.

    This board is functionally identical to the discontinued Nexys 4 DDR.
    """
    resources = nexys4ddr.Nexys4DDRPlatform.resources + [
        JTAGResource(
            0,
            tck="C4", tdi="D4", tms="D3", tdo="E5",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),
    ]


def main(_):
    top.build(NexysA7100TPlatform(), blinky.Blinky())

if __name__ == "__main__":
    app.run(main)
