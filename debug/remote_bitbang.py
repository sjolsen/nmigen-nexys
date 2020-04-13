from typing import Optional

from nmigen import *
from nmigen.build import *
from nmigen.hdl.rec import *
from nmigen.lib.fifo import SyncFIFOBuffered

from nmigen_nexys.serial import uart


class RemoteBitbang(Elaboratable):

    class UARTInterface(Record):

        def __init__(self):
            super().__init__(Layout([
                ('rx', 1, Direction.FANIN),
                ('tx', 1, Direction.FANOUT),
                ('rts', 1, Direction.FANOUT),
                ('cts', 1, Direction.FANIN),
            ]))

    class JTAGInterface(Record):

        def __init__(self):
            super().__init__(Layout([
                ('tck', 1, Direction.FANIN),
                ('tdi', 1, Direction.FANIN),
                ('tdo', 1, Direction.FANOUT),
                ('tms', 1, Direction.FANIN),
                ('trst', 1, Direction.FANIN),
                ('srst', 1, Direction.FANIN),
            ]))

    def __init__(self):
        super().__init__()
        self.uart = self.UARTInterface()
        self.jtag = self.JTAGInterface()
        self.blink = Signal(1)

    def elaborate(self, _: Optional[Platform]) -> Module:
        m = Module()
        # Frontend + FIFOs
        m.submodules.rx = rx = uart.Receive(12_000_000)
        m.submodules.rx_fifo = rx_fifo = SyncFIFOBuffered(width=8, depth=8)
        m.d.comb += [
            rx.input.eq(self.uart.rx),
            rx_fifo.w_data.eq(rx.data),
            rx_fifo.w_en.eq(rx.done),  # Masked internally by w_rdy
            self.uart.rts.eq(rx_fifo.w_rdy),
        ]
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.submodules.tx_fifo = tx_fifo = SyncFIFOBuffered(width=1, depth=8)
        m.d.comb += [
            self.uart.tx.eq(tx.output),
            tx.data.eq(Mux(tx_fifo.r_data, ord('1'), ord('0'))),
        ]
        m.d.comb += tx.start.eq(0)  # default
        m.d.comb += tx_fifo.r_en.eq(0)  # default
        with m.FSM(name='tx', reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.uart.cts & tx_fifo.r_rdy):
                    m.d.comb += tx.start.eq(1)
                    m.d.comb += tx_fifo.r_en.eq(1)
                    m.next = 'TRANSMITTING'
            with m.State('TRANSMITTING'):
                with m.If(tx.done):
                    with m.If(self.uart.cts & tx_fifo.r_rdy):
                        m.d.comb += tx.start.eq(1)
                        m.d.comb += tx_fifo.r_en.eq(1)
                        m.next = 'TRANSMITTING'
                    with m.Else():
                        m.next = 'IDLE'
        # Process incoming commands
        stall_latch = Signal(1)
        m.d.comb += rx_fifo.r_en.eq(0)  # default
        m.d.comb += tx_fifo.w_en.eq(0)  # default
        with m.FSM(name='cmd', reset='IDLE'):
            with m.State('IDLE'):
                with m.If(rx_fifo.r_rdy):
                    m.d.comb += rx_fifo.r_en.eq(1)
                    tx_data = Signal(1)
                    tx_ready = Signal(1, reset=0)
                    with m.Switch(rx_fifo.r_data):
                        wbits = Cat(self.jtag.tdi, self.jtag.tms, self.jtag.tck)
                        rbits = Cat(self.jtag.srst, self.jtag.trst)
                        with m.Case(ord('B')):
                            m.d.sync += self.blink.eq(1)
                        with m.Case(ord('b')):
                            m.d.sync += self.blink.eq(0)
                        with m.Case(ord('R')):
                            m.d.comb += tx_data.eq(self.jtag.tdo)
                            m.d.comb += tx_ready.eq(1)
                        with m.Case(ord('Q')):
                            pass
                        with m.Case('0011 0---'):
                            # ASCII '0' through '7'
                            m.d.sync += wbits.eq(rx_fifo.r_data[:3])
                        for c in 'rstu':
                            with m.Case(ord(c)):
                                m.d.sync += rbits.eq(rx_fifo.r_data - ord('r'))
                    with m.If(tx_ready):
                        with m.If(tx_fifo.w_rdy):
                            m.d.comb += tx_fifo.w_data.eq(tx_data)
                            m.d.comb += tx_fifo.w_en.eq(1)
                            m.next = 'IDLE'
                        with m.Else():
                            m.d.sync += stall_latch.eq(tx_data)
                            m.next = 'WRITE_STALL'
            with m.State('WRITE_STALL'):
                with m.If(tx_fifo.w_rdy):
                    m.d.comb += tx_fifo.w_data.eq(stall_latch)
                    m.d.comb += tx_fifo.w_en.eq(1)
                    m.next = 'IDLE'
        return m
