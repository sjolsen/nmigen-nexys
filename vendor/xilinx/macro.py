import enum
from typing import Optional

from nmigen import *
from nmigen.build import Platform


def _filter_params(params):
    return [a for a in params if a[2] is not None]


class AddSub(Elaboratable):

    class op(enum.IntEnum):
        ADD = 1
        SUBTRACT = 0

    def __init__(self, width: int, domain: Optional[str] = 'sync',
                 width_result: Optional[int] = None,
                 device: Optional[str] = '7SERIES',
                 latency: Optional[int] = None):
        super().__init__()
        self.domain = domain
        if latency is not None:
            assert 0 <= latency <= 2
        assert 1 <= width <= 48
        if width_result is not None:
            assert 1 <= width_result <= 48
        else:
            width_result = width
        # Parameters
        self.device = device
        self.latency = latency
        self.width = width
        self.width_result = width_result
        # Ports
        self.carryout = Signal(1)
        self.result = Signal(width_result)
        self.add_sub = Signal(self.op)
        self.a = Signal(width)
        self.b = Signal(width)
        self.ce = Signal(1)
        self.carryin = Signal(1)

    def elaborate(self, _: Optional[Platform]) -> Fragment:
        f = Fragment()
        params = [
            ('p', 'DEVICE', self.device),
            ('p', 'LATENCY', self.latency),
            ('p', 'WIDTH', self.width),
            ('p', 'WIDTH_RESULT', self.width_result),
        ]
        ports = [
            ('o', 'CARRYOUT', self.carryout),
            ('o', 'RESULT', self.result),
            ('i', 'ADD_SUB', self.add_sub),
            ('i', 'A', self.a),
            ('i', 'B', self.b),
            ('i', 'CE', self.ce),
            ('i', 'CARRYIN', self.carryin),
            ('i', 'CLK', ClockSignal(self.domain)),
            ('i', 'RST', ResetSignal(self.domain)),
        ]
        f.add_subfragment(Instance(
            'ADDSUB_MACRO',
            *_filter_params(params),
            *ports,
        ))
        return f
