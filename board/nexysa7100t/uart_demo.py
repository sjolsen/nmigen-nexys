"""Basic demo using the second UART channel on the integrated FTDI chip.

The UART TX and RX signals can be mirrored to a Pmod header using the
--debug_pmod flag. The flag argument is the header index: 0 indicates JA, etc.
"""

from absl import app
from absl import flags
from nmigen import *
from nmigen.build import *

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.serial import uart

flags.DEFINE_integer('debug_pmod', None, 'Pmod header to use for debugging')

FLAGS = flags.FLAGS


class ASCIIRenderer(Elaboratable):
    """Response rendering pipeline."""

    TEMPLATE = b"'X' = 0xXX\r\n"

    def _hexdigit(self, x: Value) -> Value:
        return Mux(x < 10, ord('0') | x, ord('@') | (x - 9))

    def __init__(self):
        super().__init__()
        self.input = Signal(8)
        self.output = [Signal(8) for _ in range(len(self.TEMPLATE))]
        self.start = Signal()
        self.done = Signal(reset=0)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.d.comb += self.done.eq(self.start)
        for out, template in zip(self.output, self.TEMPLATE):
            m.d.comb += out.eq(template)
        m.d.comb += self.output[1].eq(self.input)
        m.d.comb += self.output[8].eq(self._hexdigit(self.input[4:8]))
        m.d.comb += self.output[9].eq(self._hexdigit(self.input[0:4]))
        return m


class UARTDemo(Elaboratable):
    """Simple call-and-response demo.

    This demo takes each character received as input and sends back a formatted
    message showing the character and its ASCII representation. For example,
    when receiving the character 'A', it will respond:

        'A' = 0x41

    Input buffering is currently not implemented, so immediately consecutive
    characters are likely to be dropped.
    """

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
                # TODO: This will drop input until the last transmission is done
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
    """Pull the TX/RX signals out to a Pmod header for debugging."""

    def elaborate(self, platform: Platform) -> Module:
        m = super().elaborate(platform)
        debug = platform.request('debug')
        m.d.comb += debug.tx.eq(self.pins.tx)
        m.d.comb += debug.rx.eq(self.pins.rx)
        return m


def main(_):
    platform = nexysa7100t.NexysA7100TPlatform()
    if FLAGS.debug_pmod is not None:
        conn = ('pmod', FLAGS.debug_pmod)
        platform.add_resources([
            Resource(
                'debug', 0,
                Subsignal('tx', Pins('1', conn=conn, dir='o')),
                Subsignal('rx', Pins('2', conn=conn, dir='o')),
                Attrs(IOSTANDARD="LVCMOS33")),
        ])
        demo_cls = UARTDemoDebug
    else:
        demo_cls = UARTDemo
    top.build(platform, demo_cls(pins=platform.request('uart')))

if __name__ == "__main__":
    app.run(main)
