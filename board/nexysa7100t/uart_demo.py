from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import top
from nmigen_nexys.core import util
from nmigen_nexys.math import lut
from nmigen_nexys.serial import uart


class ASCIILUT(Elaboratable):

    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.data = text.encode('ascii')
        self.input = Signal(range(len(self.data)), reset=0)
        self.output = Signal(7)

    def _lookup(self, i: int) -> int:
        if i < len(self.data):
            return self.data[i]
        else:
            return 0

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        m.submodules.byte_lut = lut.FunctionLUT(self._lookup, self.input,
                                                self.output)
        return m


class UARTDemo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        pins = platform.request('uart')
        m.d.comb += pins.rts.eq(pins.cts)

        m.submodules.timer = timer = timer_module.UpTimer(
            util.GetClockFreq(platform))
        m.submodules.text = text = ASCIILUT('Hello, world!\r\n')
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.d.comb += tx.data.eq(text.output)
        m.d.comb += pins.tx.eq(tx.output)

        m.d.sync += tx.start.eq(0)  # default
        with m.FSM(reset='START'):
            with m.State('START'):
                m.d.sync += text.input.eq(0)
                m.d.sync += tx.start.eq(1)
                m.next = 'PRINT'
            with m.State('PRINT'):
                with m.If(tx.done):
                    with m.If(text.input < len(text.data) - 1):
                        m.d.sync += text.input.eq(text.input + 1)
                        m.d.sync += tx.start.eq(1)
                    with m.Else():
                        m.next = 'IDLE'
            with m.State('IDLE'):
                with m.If(timer.triggered):
                    m.next = 'START'
        return m


if __name__ == "__main__":
    top.main(nexysa7100t.NexysA7100TPlatform(), UARTDemo())
