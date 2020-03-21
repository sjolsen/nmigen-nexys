from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import Direction, Layout, Record


class FF(Elaboratable):

    class Interface(Record):

        def __init__(self, width: int, reset=None):
            fields = {'q': Signal(width, reset=reset)} if reset is not None else None
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
