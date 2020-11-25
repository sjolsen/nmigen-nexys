"""Simple demo for the ULX3S (85F variant)."""

from absl import app
from nmigen_boards import ulx3s
from nmigen_boards.test import blinky

from nmigen_nexys.bazel import top


def main(_):
    top.build(ulx3s.ULX3S_85F_Platform(), blinky.Blinky())

if __name__ == "__main__":
    app.run(main)
