from typing import Iterable, NamedTuple, Optional

from minerva import wishbone
from nmigen import *
from nmigen.build import *
from nmigen.hdl.mem import *
from nmigen.hdl.ast import Statement
from nmigen.hdl.rec import Record
from rules_python.python.runfiles import runfiles

from nmigen_nexys.core import util
from nmigen_nexys.display import seven_segment
from nmigen_nexys.vendor.xilinx import macro


class WishboneMux(Elaboratable):

    class Port(NamedTuple):
        name: str
        start: int
        size: int
        wbus: Record

    PortLike = util.LikeNamedTuple('WishboneMux.Port')

    def __init__(self, ports: Iterable['WishboneMux.PortLike'] = ()):
        super().__init__()
        self.ports = []
        self.wbus = Record(wishbone.wishbone_layout)
        for port in ports:
            self.add_port(port)

    def add_port(self, port: 'WishboneMux.PortLike'):
        port = WishboneMux.Port._make(port)
        assert bin(port.size).count('1') == 1
        assert port.size >= 4
        assert port.start % port.size == 0
        for other in self.ports:
            assert port.name != other.name
            before = port.start + port.size <= other.start
            after = other.start + other.size <= port.start
            assert before or after
        self.ports.append(port)

    def elaborate(self, _: Optional[Platform]) -> Module:
        m = Module()
        addressed_signals = []
        for port in self.ports:
            # Better debug naming
            pbus = Record.like(port.wbus, name=port.name)
            m.d.comb += pbus.connect(port.wbus)
            mask32 = ~(port.size - 1)
            mask30 = mask32 >> 2
            addressed = Signal(name=f'addressed_{port.name}')
            m.d.comb += addressed.eq(
                (self.wbus.adr & mask30) == port.start >> 2)
            addressed_signals.append(addressed)
            m.d.comb += [
                pbus.adr.eq(self.wbus.adr),
                pbus.dat_w.eq(self.wbus.dat_w),
                pbus.sel.eq(self.wbus.sel),
                pbus.stb.eq(self.wbus.stb),
                pbus.we.eq(self.wbus.we),
                pbus.cti.eq(self.wbus.cti),
                pbus.bte.eq(self.wbus.bte),
            ]
            with m.If(addressed):
                m.d.comb += [
                    pbus.cyc.eq(self.wbus.cyc),
                    self.wbus.dat_r.eq(pbus.dat_r),
                    self.wbus.ack.eq(pbus.ack),
                    self.wbus.err.eq(pbus.err),
                ]
        with m.If(self.wbus.cyc & ~Cat(*addressed_signals).any()):
            m.d.comb += self.wbus.err.eq(1)
        return m


class DualPortBRAM(Elaboratable):

    def __init__(self, *,
                 read_only: bool = False,
                 init_file: Optional[str] = None,
                 init: Optional[bytes] = None):
        super().__init__()
        self.read_only = read_only
        self.bytes = self._init_bytes(init_file, init)
        self.abus = Record(wishbone.wishbone_layout)
        self.bbus = Record(wishbone.wishbone_layout)

    def _init_bytes(self, init_file: Optional[str],
                    init: Optional[bytes]) -> bytes:
        if init is not None:
            return init
        elif init_file is not None:
            with open(init_file, 'rb') as f:
                return f.read()
        else:
            return bytes()

    def _connect_memory(self, m: Module, wbus: Record, rport: ReadPort,
                        wport: WritePort):
        # Inspired by Wishbone B4 8.7.2
        strobe = wbus.cyc & wbus.stb
        write = Mux(strobe & wbus.we, wbus.sel, 0)
        will_ack = Signal()
        will_err = Signal()
        m.d.comb += [
            rport.addr.eq(wbus.adr),
            wport.addr.eq(wbus.adr),
            wport.data.eq(wbus.dat_w),
            wport.en.eq(0 if self.read_only else write),
            wbus.dat_r.eq(rport.data),
            will_ack.eq(strobe & ~will_err),
            will_err.eq(write.any() if self.read_only else 0),
        ]
        m.d.sync += [
            wbus.ack.eq(will_ack),
            wbus.err.eq(will_err),
        ]

    def elaborate(self, _: Optional[Platform]) -> Module:
        if len(self.bytes) % 4 != 0:
            self.bytes.extend([0] * (4 - len(self.bytes) % 4))
        init_words = []
        for i in range(len(self.bytes) // 4):
            wbytes = self.bytes[i * 4:(i + 1) * 4]
            init_words.append(int.from_bytes(wbytes, byteorder='little'))
        m = Module()
        # TODO: Revert to 4 kiB when https://github.com/nmigen/nmigen/issues/359
        #   is fixed
        # mem = Memory(width=32, depth=4 * 1024, init=init_words)
        mem = Memory(width=32, depth=0x800, init=init_words[:0xC00 // 4])
        m.submodules.ar = ar = mem.read_port(transparent=True)
        m.submodules.aw = aw = mem.write_port(granularity=8)
        m.submodules.br = br = mem.read_port(transparent=True)
        m.submodules.bw = bw = mem.write_port(granularity=8)
        self._connect_memory(m, self.abus, ar, aw)
        self._connect_memory(m, self.bbus, br, bw)
        return m


class XilinxDualPortBRAM(DualPortBRAM):

    def _connect_fasm(self, m: Module, wbus: Record,
                      port: macro.TrueDualPortRAM.Port):
        # Inspired by Wishbone B4 8.7.2
        strobe = wbus.cyc & wbus.stb
        write = Mux(strobe & wbus.we, wbus.sel, 0)
        will_ack = Signal()
        will_err = Signal()
        m.d.comb += [
            port.addr.eq(wbus.adr),
            port.di.eq(wbus.dat_w),
            port.en.eq(strobe),
            port.we.eq(0 if self.read_only else write),
            wbus.dat_r.eq(port.do),
            will_ack.eq(strobe & ~will_err),
            will_err.eq(write.any() if self.read_only else 0),
        ]
        m.d.sync += [
            wbus.ack.eq(will_ack),
            wbus.err.eq(will_err),
        ]

    def elaborate(self, platform: Optional[Platform]) -> Module:
        if platform is None:
            # Simulation
            return super().elaborate(platform)
        m = Module()
        m.submodules.bram = bram = macro.TrueDualPortRAM(
            bram_size='36Kb',
            port_a=macro.TrueDualPortRAM.Port(read_width=32, write_width=32),
            port_b=macro.TrueDualPortRAM.Port(read_width=32, write_width=32),
            init=self.bytes.ljust(4 * 1024, b'\0'))
        self._connect_fasm(m, self.abus, bram.port_a)
        self._connect_fasm(m, self.bbus, bram.port_b)
        return m


class WishboneRegisters(Elaboratable):

    class Reg(NamedTuple):
        name: str
        start: int
        size: int  # TODO(python-3.8): Literal[1, 2, 4]
        init: int

    RegLike = util.LikeNamedTuple('WishboneRegisters.Reg')

    def __init__(self, size: int,
                 regs: Iterable['WishboneRegisters.RegLike'] = ()):
        super().__init__()
        self.size = size
        self.registers = []
        self.wbus = Record(wishbone.wishbone_layout)
        self._by_name = {}
        for reg in regs:
            self.add_register(reg)

    def add_register(self, reg: 'WishboneRegisters.RegLike'):
        reg = WishboneRegisters.Reg._make(reg)
        assert reg.size in (4,)  # TODO: 1, 2
        assert reg.start % reg.size == 0
        for other in self.registers:
            assert reg.name != reg.name
            assert reg.start + reg.size <= self.size
            before = reg.start + reg.size <= other.start
            after = other.start + other.size <= reg.start
            assert before or after
        self.registers.append(reg)
        self._by_name[reg.name] = Signal(reg.size * 8, name=reg.name)

    def __getattr__(self, name):
        try:
            return self._by_name[name]
        except KeyError as e:
            raise AttributeError from e

    def elaborate(self, _: Optional[Platform]) -> Module:
        m = Module()
        active = Signal()
        write = Signal()
        m.d.comb += active.eq(self.wbus.cyc & self.wbus.stb)
        m.d.comb += write.eq(active & self.wbus.we)
        addressed_signals = []
        periph_mask32 = self.size - 1
        for reg in self.registers:
            mask32 = periph_mask32 & ~(reg.size - 1)
            mask30 = mask32 >> 2
            addressed = Signal(name=f'addressed_{reg.name}')
            m.d.comb += addressed.eq(
                (self.wbus.adr & mask30) == reg.start >> 2)
            addressed_signals.append(addressed)
            storage = self._by_name[reg.name]
            with m.If(addressed & active):
                m.d.comb += self.wbus.dat_r.eq(storage)
            with m.If(addressed & write):
                wmask = Signal(32)
                m.d.comb += wmask.eq(Cat(
                    *(Repl(self.wbus.sel[i], 8) for i in range(4))))
                old = storage & ~wmask
                new = self.wbus.dat_w & wmask
                m.d.sync += storage.eq(old | new)
        with m.If(active):
            m.d.comb += self.wbus.ack.eq(Cat(*addressed_signals).any())
            m.d.comb += self.wbus.err.eq(~self.wbus.ack)
        return m


class SevenSegmentDisplay(Elaboratable):

    def __init__(self, output: seven_segment.DisplayBank):
        super().__init__()
        self.output = output
        self.wbus = Record(wishbone.wishbone_layout)

    def elaborate(self, _: Optional[Platform]) -> Module:
        m = Module()
        m.submodules.regs = regs = WishboneRegisters(
            size=0x100,
            regs=[('data', 0x00, 4, 0x0000_0000)])
        m.d.comb += self.wbus.connect(regs.wbus)
        m.submodules.digit = digit = seven_segment.HexDigitLUT()
        digits = Array(regs.data[4*i:4*(i+1)] for i in range(8))
        m.submodules.mux = mux = seven_segment.DisplayMultiplexer(self.output)
        m.d.comb += digit.input.eq(digits[mux.select])
        m.d.comb += mux.segments.eq(digit.output)
        m.d.comb += mux.duty_cycle.eq(-1)
        return m


class Peripherals(Elaboratable):

    def __init__(self):
        super().__init__()
        self.segments = Signal(8)
        self.anodes = Signal(8)
        self.ibus = Record(wishbone.wishbone_layout)
        self.dbus = Record(wishbone.wishbone_layout)

    def elaborate(self, _: Optional[Platform]) -> Module:
        m = Module()
        # Set up ROM/RAM peripherals
        r = runfiles.Create()
        m.submodules.rom = rom = XilinxDualPortBRAM(
            read_only=True,
            init_file=r.Rlocation(
                'nmigen_nexys/board/nexysa7100t/riscv_demo/start.bin'))
        m.submodules.ram = ram = XilinxDualPortBRAM()
        # Set up the display peripheral
        bank = seven_segment.DisplayBank()
        m.d.comb += self.segments.eq(bank.segments)
        m.d.comb += self.anodes.eq(bank.anodes)
        m.submodules.sseg = sseg = SevenSegmentDisplay(bank)
        # Connect peripherals to the instruction and data buses
        m.d.comb += self.ibus.connect(rom.abus)
        m.submodules.dmux = dmux = WishboneMux((
            ('rom', 0x00000000, 4 * 1024, rom.bbus),
            ('ram', 0x00001000, 4 * 1024, ram.abus),
            ('sseg', 0x00002000, 0x100, sseg.wbus),
        ))
        m.d.comb += self.dbus.connect(dmux.wbus)
        return m
