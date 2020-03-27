"""Basic flip-flop definitions."""

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import Direction, Layout, Record


class FF(Elaboratable):
    """Flip-flop with a muxable interface."""

    class Interface(Record):
        """Muxable interface for nmigen_nexys.core.flop.FF."""

        def __init__(self, width: int, reset=None):
            if reset is not None:
                fields = {'q': Signal(width, reset=reset)}
            else:
                fields = None
            super().__init__(Layout([
                ('d', width, Direction.FANIN),
                ('q', width, Direction.FANOUT),
                ('clk_en', 1, Direction.FANIN),
            ]), fields=fields)

    def __init__(self, width: int, reset=None):
        super().__init__()
        self.interface = FF.Interface(width, reset=reset)
        self.q = self.interface.q

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        with m.If(self.interface.clk_en):
            m.d.sync += self.interface.q.eq(self.interface.d)
        return m
