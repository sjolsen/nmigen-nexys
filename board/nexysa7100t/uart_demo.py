from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import top
from nmigen_nexys.math import bcd
from nmigen_nexys.serial import uart


class ASCIIRenderer(Elaboratable):

    # TODO: Base 10 needs 3 digits...
    TEMPLATE = b"'X' = XX\r\n"

    def __init__(self):
        super().__init__()
        self.input = Signal(8)
        self.output = [Signal(8) for _ in range(len(self.TEMPLATE))]
        self.start = Signal()
        self.done = Signal(reset=0)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.submodules.bin2bcd = bin2bcd = bcd.BinToBCD(
            input=self.input, output=[Signal(4) for _ in range(2)])
        m.d.comb += bin2bcd.start.eq(self.start)
        m.d.comb += self.done.eq(bin2bcd.done)
        for out, template in zip(self.output, self.TEMPLATE):
            m.d.comb += out.eq(template)
        m.d.comb += self.output[1].eq(self.input)
        m.d.comb += self.output[6].eq(
            Mux(bin2bcd.output[1], ord('0') | bin2bcd.output[1], ord(' ')))
        m.d.comb += self.output[7].eq(ord('0') | bin2bcd.output[0])
        return m


# TODO: It works... most of the time
class UARTDemo(Elaboratable):

    def __init__(self, pins: Record):
        super().__init__()
        self.pins = pins

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.d.comb += self.pins.rts.eq(self.pins.cts)

        baud_rate = 12_000_000
        m.submodules.tx = tx = uart.Transmit(baud_rate)
        m.submodules.rx = rx = uart.Receive(baud_rate)
        m.d.comb += self.pins.tx.eq(tx.output)
        m.d.comb += rx.input.eq(self.pins.rx)

        m.submodules.render = render = ASCIIRenderer()
        output = Signal(8 * len(render.output))
        m.d.comb += tx.data.eq(output[0:8])

        m.d.sync += render.start.eq(0)  # default
        m.d.sync += tx.start.eq(0)  # default
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(rx.done):
                    m.d.sync += render.input.eq(rx.data)
                    m.d.sync += render.start.eq(1)
                    m.next = 'RENDER'
            with m.State('RENDER'):
                with m.If(render.done):
                    m.d.sync += output.eq(Cat(*render.output))
                    m.d.sync += tx.start.eq(1)
                    m.next = 'TRANSMIT'
            with m.State('TRANSMIT'):
                with m.If(tx.done):
                    with m.If(output[8:24].any()):
                        m.d.sync += output.eq(output >> 8)
                        m.d.sync += tx.start.eq(1)
                    with m.Else():
                        m.next = 'IDLE'
        return m


class UARTDemoDebug(UARTDemo):

    def elaborate(self, platform: Platform) -> Module:
        m = super().elaborate(platform)
        debug = platform.request('debug')
        m.d.comb += debug.tx.eq(self.pins.tx)
        m.d.comb += debug.rx.eq(self.pins.rx)
        return m


if __name__ == "__main__":
    platform = nexysa7100t.NexysA7100TPlatform()
    platform.add_resources([
        Resource(
            'debug', 0,
            Subsignal('tx', Pins('1', conn=('pmod', 3), dir='o')),
            Subsignal('rx', Pins('2', conn=('pmod', 3), dir='o')),
            Attrs(IOSTANDARD="LVCMOS33")),
    ])
    top.main(platform, UARTDemoDebug(pins=platform.request('uart')))
