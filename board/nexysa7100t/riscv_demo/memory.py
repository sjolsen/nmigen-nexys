from typing import List, Optional

from minerva import wishbone
from nmigen import *
from nmigen.build import *
from nmigen.hdl.ast import Statement
from nmigen.hdl.rec import Record

from nmigen_nexys.vendor.xilinx import macro


class RAM(Elaboratable):

    def __init__(self):
        super().__init__()
        self.ibus = Record(wishbone.wishbone_layout)
        self.dbus = Record(wishbone.wishbone_layout)

    def _connect_fasm(self, wbus: Record,
                      port: macro.TrueDualPortRAM.Port) -> List[Statement]:
        # Inspired by Wishbone B4 8.7.2
        return [
            port.addr.eq(wbus.adr),
            port.di.eq(wbus.dat_w),
            port.en.eq(wbus.stb),
            port.we.eq(Mux(wbus.stb & wbus.we, wbus.sel, 0)),
            wbus.dat_r.eq(port.do),
            wbus.ack.eq(wbus.stb),
        ]

    def elaborate(self, _: Optional[Platform]) -> Module:
        m = Module()
        nop = 0x13.to_bytes(4, byteorder='little')
        m.submodules.bram = bram = macro.TrueDualPortRAM(
            bram_size='36Kb',
            port_a=macro.TrueDualPortRAM.Port(read_width=32, write_width=32),
            port_b=macro.TrueDualPortRAM.Port(read_width=32, write_width=32),
            init=nop * 1024)
        m.d.comb += self._connect_fasm(self.ibus, bram.port_a)
        m.d.comb += self._connect_fasm(self.dbus, bram.port_b)
        return m
