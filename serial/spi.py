"""Implementation of https://en.wikipedia.org/wiki/Serial_Peripheral_Interface."""

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import timer


class Bus(Record):
    """SPI bus as seen from the master."""

    LAYOUT = Layout([
        ('clk', 1),
        ('cs_n', 1),
        ('mosi', 1),
        ('miso', 1),
    ])

    def __init__(
            self, clk: Signal, cs_n: Signal, mosi: Signal, miso: Signal,
            freq_Hz: int):
        super().__init__(self.LAYOUT, fields={
            'clk': clk,
            'cs_n': cs_n,
            'mosi': mosi,
            'miso': miso,
        })
        self.freq_Hz = freq_Hz


class MOSISource(Record):
    """Source for MOSI data.

    When a transaction is initiated, the SPI master will pull data from this
    interface on demand. After reading data, it will strobe next and decrement
    count. When count reaches zero, the transaction will finish.
    """

    def __init__(self, bit_depth: int):
        layout = Layout([
            ('data', 1),
            ('next', 1),
            ('count', range(bit_depth)),
        ])
        super().__init__(layout)


class MISOSink(Record):
    """Sink for MISO data.

    When the SPI master clocks in a bit, it will make it available via data and
    strobe ready.
    """

    LAYOUT = Layout([
        ('data', 1),
        ('ready', 1),
    ])

    def __init__(self):
        super().__init__(self.LAYOUT)


class Master(Elaboratable):
    """SPI master implementation."""

    def __init__(self, bus: Bus, source: MOSISource, sink: MISOSink):
        super().__init__()
        self.bus = bus
        self.source = source
        self.sink = sink
        self.start = Signal(reset=0)
        self.busy = Signal(reset=0)
        self.done = Signal(reset=0)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        # Set up a timer to start when start is strobed and run at twice the
        # bus frequency until the transaction ends
        m.submodules.hclk_timer = hclk_timer = timer.OneShot(
            platform.platform.default_clk_frequency // (2 * self.bus.freq_Hz))
        m.d.comb += hclk_timer.go.eq(
            self.start | (self.busy & hclk_timer.triggered))
        with m.If(self.start):
            m.d.sync += self.busy.eq(1)
        with m.If(self.done):
            m.d.sync += self.busy.eq(0)
        return m
