import enum
import os
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


class TrueDualPortRAM(Elaboratable):

    _WIDTH_TABLE = (
        # UG953 pp28-30
        # (write_width, read_width, bram_size) : (addr.width, we.width)
        # ---
        ((range(19, 36 + 1), range(19, 36 + 1), '36Kb'), (10, 4)),
        ((range(19, 36 + 1), range(10, 18 + 1), '36Kb'), (11, 4)),
        ((range(19, 36 + 1), range(5, 9 + 1), '36Kb'), (12, 4)),
        ((range(19, 36 + 1), range(3, 4 + 1), '36Kb'), (13, 4)),
        ((range(19, 36 + 1), range(2, 2 + 1), '36Kb'), (14, 4)),
        ((range(19, 36 + 1), range(1, 1 + 1), '36Kb'), (15, 4)),
        # ---
        ((range(10, 18 + 1), range(19, 36 + 1), '36Kb'), (11, 2)),
        ((range(10, 18 + 1), range(10, 18 + 1), '36Kb'), (11, 2)),
        ((range(10, 18 + 1), range(5, 9 + 1), '36Kb'), (12, 2)),
        ((range(10, 18 + 1), range(3, 4 + 1), '36Kb'), (13, 2)),
        ((range(10, 18 + 1), range(2, 2 + 1), '36Kb'), (14, 2)),
        ((range(10, 18 + 1), range(1, 1 + 1), '36Kb'), (15, 2)),
        # ---
        ((range(5, 9 + 1), range(19, 36 + 1), '36Kb'), (12, 1)),
        ((range(5, 9 + 1), range(10, 18 + 1), '36Kb'), (12, 1)),
        ((range(5, 9 + 1), range(5, 9 + 1), '36Kb'), (12, 1)),
        ((range(5, 9 + 1), range(3, 4 + 1), '36Kb'), (13, 1)),
        ((range(5, 9 + 1), range(2, 2 + 1), '36Kb'), (14, 1)),
        ((range(5, 9 + 1), range(1, 1 + 1), '36Kb'), (15, 1)),
        # ---
        ((range(3, 4 + 1), range(19, 36 + 1), '36Kb'), (13, 1)),
        ((range(3, 4 + 1), range(10, 18 + 1), '36Kb'), (13, 1)),
        ((range(3, 4 + 1), range(5, 9 + 1), '36Kb'), (13, 1)),
        ((range(3, 4 + 1), range(3, 4 + 1), '36Kb'), (13, 1)),
        ((range(3, 4 + 1), range(2, 2 + 1), '36Kb'), (14, 1)),
        ((range(3, 4 + 1), range(1, 1 + 1), '36Kb'), (15, 1)),
        # ---
        ((range(2, 2 + 1), range(19, 36 + 1), '36Kb'), (14, 1)),
        ((range(2, 2 + 1), range(10, 18 + 1), '36Kb'), (14, 1)),
        ((range(2, 2 + 1), range(5, 9 + 1), '36Kb'), (14, 1)),
        ((range(2, 2 + 1), range(3, 4 + 1), '36Kb'), (14, 1)),
        ((range(2, 2 + 1), range(2, 2 + 1), '36Kb'), (14, 1)),
        ((range(2, 2 + 1), range(1, 1 + 1), '36Kb'), (15, 1)),
        # ---
        ((range(1, 1 + 1), range(19, 36 + 1), '36Kb'), (15, 1)),
        ((range(1, 1 + 1), range(10, 18 + 1), '36Kb'), (15, 1)),
        ((range(1, 1 + 1), range(5, 9 + 1), '36Kb'), (15, 1)),
        ((range(1, 1 + 1), range(3, 4 + 1), '36Kb'), (15, 1)),
        ((range(1, 1 + 1), range(2, 2 + 1), '36Kb'), (15, 1)),
        ((range(1, 1 + 1), range(1, 1 + 1), '36Kb'), (15, 1)),
        # ---
        ((range(10, 18 + 1), range(10, 18 + 1), '18Kb'), (10, 2)),
        ((range(10, 18 + 1), range(5, 9 + 1), '18Kb'), (11, 2)),
        ((range(10, 18 + 1), range(3, 4 + 1), '18Kb'), (12, 2)),
        ((range(10, 18 + 1), range(2, 2 + 1), '18Kb'), (13, 2)),
        ((range(10, 18 + 1), range(1, 1 + 1), '18Kb'), (14, 2)),
        # ---
        ((range(5, 9 + 1), range(10, 18 + 1), '18Kb'), (11, 1)),
        ((range(5, 9 + 1), range(5, 9 + 1), '18Kb'), (11, 1)),
        ((range(5, 9 + 1), range(3, 4 + 1), '18Kb'), (12, 1)),
        ((range(5, 9 + 1), range(2, 2 + 1), '18Kb'), (13, 1)),
        ((range(5, 9 + 1), range(1, 1 + 1), '18Kb'), (14, 1)),
        # ---
        ((range(3, 4 + 1), range(10, 18 + 1), '18Kb'), (12, 1)),
        ((range(3, 4 + 1), range(5, 9 + 1), '18Kb'), (12, 1)),
        ((range(3, 4 + 1), range(3, 4 + 1), '18Kb'), (12, 1)),
        ((range(3, 4 + 1), range(2, 2 + 1), '18Kb'), (13, 1)),
        ((range(3, 4 + 1), range(1, 1 + 1), '18Kb'), (14, 1)),
        # ---
        ((range(2, 2 + 1), range(10, 18 + 1), '18Kb'), (13, 1)),
        ((range(2, 2 + 1), range(5, 9 + 1), '18Kb'), (13, 1)),
        ((range(2, 2 + 1), range(3, 4 + 1), '18Kb'), (13, 1)),
        ((range(2, 2 + 1), range(2, 2 + 1), '18Kb'), (13, 1)),
        ((range(2, 2 + 1), range(1, 1 + 1), '18Kb'), (14, 1)),
        # ---
        ((range(1, 1 + 1), range(10, 18 + 1), '18Kb'), (14, 1)),
        ((range(1, 1 + 1), range(5, 9 + 1), '18Kb'), (14, 1)),
        ((range(1, 1 + 1), range(3, 4 + 1), '18Kb'), (14, 1)),
        ((range(1, 1 + 1), range(2, 2 + 1), '18Kb'), (14, 1)),
        ((range(1, 1 + 1), range(1, 1 + 1), '18Kb'), (14, 1)),
    )

    class Port(object):

        def __init__(
                self,
                domain: Optional[str] = 'sync',
                do_reg: Optional[int] = None,
                init: Optional[int] = None,
                # TODO: See if you can actually get away with an unspecified
                #   width. The default value is zero which is not a legal value
                read_width: Optional[int] = None,
                srval: Optional[int] = None,
                # TODO(python-3.8): Literal['WRITE_FIRST', 'READ_FIRST', 'NO_CHANGE']
                write_mode: Optional[str] = None,
                write_width: Optional[int] = None):
            super().__init__()
            self.domain = domain
            # Parameters
            self.bram_size = None
            if do_reg is not None:
                assert do_reg in (0, 1)
            self.do_reg = do_reg
            self.init = init
            if read_width is not None:
                assert 1 <= read_width <= 36
            self.read_width = read_width
            self.srval = srval
            if write_mode is not None:
                assert write_mode in ('WRITE_FIRST', 'READ_FIRST', 'NO_CHANGE')
            self.write_mode = write_mode
            if write_width is not None:
                assert 1 <= write_width <= 36
            self.write_width = write_width
            # Ports
            self.do = Signal(read_width)
            self.addr = None  # Dependent on bram_size
            self.di = Signal(write_width)
            self.en = Signal()
            self.regce = Signal()
            self.we = None  # Dependent on bram_size

        def _finalize(self, bram_size):
            self.bram_size = bram_size
            # (write_width, read_width, bram_size) : (addr.width, we.width)
            for k, (addr_width, we_width) in TrueDualPortRAM._WIDTH_TABLE:
                ww_match = self.write_width in k[0]
                rw_match = self.read_width in k[1]
                br_match = bram_size == k[2]
                if ww_match and rw_match and br_match:
                    self.addr = Signal(addr_width)
                    self.we = Signal(we_width)
                    break
            else:
                raise RuntimeError(
                    f'Illegal combination of write_width={self.write_width}, '
                    f'read_width={self.read_width}, and '
                    f'bram_size={self.bram_size}')

    def __init__(
            self,
            # TODO(python-3.8): Literal['18Kb', '36Kb']
            bram_size: Optional[str] = None,
            device: Optional[str] = '7SERIES',
            port_a: Optional['TrueDualPortRAM.Port'] = None,
            port_b: Optional['TrueDualPortRAM.Port'] = None,
            init_file: Optional[str] = None,
            init: Optional[bytes] = None,
            # TODO(python-3.8): Literal['ALL', 'WARNING_ONLY', 'GENERATE_X_ONLY', 'NONE']
            sim_collision_check: Optional[str] = None,
            initp: Optional[bytes] = None):
        super().__init__()
        if bram_size is not None:
            assert bram_size in ('18Kb', '36Kb')
        port_a = port_a or self.Port()
        port_a._finalize(bram_size)
        self.port_a = port_a
        port_b = port_b or self.Port()
        port_b._finalize(bram_size)
        self.port_b = port_b
        # Parameters
        self.bram_size = bram_size
        self.device = device
        assert not (init_file is not None and init is not None)
        if init_file is not None:
            assert os.path.exists(init_file)
        self.init_file = init_file
        if init is not None:
            if bram_size == '18Kb':
                assert len(init) == 0x40 * 32  # 0x40 rows of 256 bits
            elif bram_size == '36Kb':
                assert len(init) == 0x80 * 32  # 0x80 rows of 256 bits
            else:
                assert False
        self.init = init
        if sim_collision_check:
            assert sim_collision_check in (
                'ALL', 'WARNING_ONLY', 'GENERATE_X_ONLY', 'NONE')
        self.sim_collision_check = sim_collision_check
        if initp is not None:
            if bram_size == '18Kb':
                assert len(initp) == 0x08 * 32  # 0x08 rows of 256 bits
            elif bram_size == '36Kb':
                assert len(initp) == 0x10 * 32  # 0x10 rows of 256 bits
            else:
                assert False
        self.initp = initp

    def elaborate(self, _: Optional[Platform]) -> Fragment:
        f = Fragment()
        params = [
            ('p', 'BRAM_SIZE', self.bram_size),
            ('p', 'DEVICE', self.device),
            ('p', 'DOA_REG', self.port_a.do_reg),
            ('p', 'DOB_REG', self.port_b.do_reg),
            ('p', 'INIT_A', self.port_a.init),
            ('p', 'INIT_B', self.port_b.init),
            ('p', 'INIT_FILE', self.init_file),
            ('p', 'READ_WIDTH_A', self.port_a.read_width),
            ('p', 'READ_WIDTH_B', self.port_b.read_width),
            ('p', 'SIM_COLLISION_CHECK', self.sim_collision_check),
            ('p', 'SRVAL_A', self.port_a.srval),
            ('p', 'SRVAL_B', self.port_b.srval),
            ('p', 'WRITE_MODE_A', self.port_a.write_mode),
            ('p', 'WRITE_MODE_B', self.port_b.write_mode),
            ('p', 'WRITE_WIDTH_A', self.port_a.write_width),
            ('p', 'WRITE_WIDTH_B', self.port_b.write_width),
        ]
        def get_row(data, i):
            row_bytes = data[i * 32:(i + 1) * 32]
            return int.from_bytes(row_bytes, byteorder='little')
        if self.init is not None:
            params.extend([
                # TODO: Do bytes work here???
                # Literal initialization data is broken up into rows of 256 bits
                ('p', f'INIT_{i:02X}', get_row(self.init, i))
                for i in range(len(self.init) // 32)
            ])
        if self.initp is not None:
            params.extend([
                # TODO: Do bytes work here???
                # Literal initialization data is broken up into rows of 256 bits
                ('p', f'INITP_{i:02X}', get_row(self.initp, i))
                for i in range(len(self.initp) // 32)
            ])
        ports = [
            ('o', 'DOA', self.port_a.do),
            ('o', 'DOB', self.port_b.do),
            ('i', 'ADDRA', self.port_a.addr),
            ('i', 'ADDRB', self.port_b.addr),
            ('i', 'CLKA', ClockSignal(self.port_a.domain)),
            ('i', 'CLKB', ClockSignal(self.port_b.domain)),
            ('i', 'DIA', self.port_a.di),
            ('i', 'DIB', self.port_b.di),
            ('i', 'ENA', self.port_a.en),
            ('i', 'ENB', self.port_b.en),
            ('i', 'REGCEA', self.port_a.regce),
            ('i', 'REGCEB', self.port_b.regce),
            ('i', 'RSTA', ResetSignal(self.port_a.domain)),
            ('i', 'RSTB', ResetSignal(self.port_b.domain)),
            ('i', 'WEA', self.port_a.we),
            ('i', 'WEB', self.port_b.we),
        ]
        f.add_subfragment(Instance(
            'BRAM_TDP_MACRO',
            *_filter_params(params),
            *ports,
        ))
        return f
