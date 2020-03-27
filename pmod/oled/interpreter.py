"""Command-based FSM generator for the Pmod OLED."""

import abc
from typing import Iterable, List, NamedTuple

from nmigen import *
from nmigen.build import *
from nmigen.hdl.ast import Assign

from nmigen_nexys.core import flop
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import util
from nmigen_nexys.display import ssd1306


class Command(abc.ABC):
    """Command base class consumed by Program."""

    def __init__(self):
        super().__init__()
        self.addr = None

    def __repr__(self) -> str:
        return util.ProductRepr(self)

    @property
    def state(self) -> str:
        """Generate a human-readable label for use as an FSM string.

        The state string contains the command's address, if set, and a
        representation of the command object similar to what you'd write in
        Python to construct it. See util.ProductRepr for details.
        """
        addr = str(self.addr) if self.addr is not None else '<unknown>'
        return f'{addr}@{repr(self)}'

    def SetAddress(self, addr: int):
        """Used internally to record the command's index in the program."""
        assert self.addr is None
        self.addr = addr

    @abc.abstractmethod
    def Start(self, ctx: 'Program.Context') -> Iterable[Assign]:
        """Sync macro to initiate the command."""

    @abc.abstractmethod
    def ReleaseStart(self, ctx: 'Program.Context') -> Iterable[Assign]:
        """Sync macro to release any strobe signals from Start."""

    @abc.abstractmethod
    def Poll(self, ctx: 'Program.Context') -> Value:
        """Value macro determine whether the command is complete."""


class DigitalWrite(Command):
    """Update the value of a flip-flop, e.g. one connected to an output pin."""

    def __init__(self, ff: flop.FF.Interface, value: Value):
        super().__init__()
        self.ff = ff
        self.value = value

    def Start(self, ctx: 'Program.Context') -> Iterable[Assign]:
        yield self.ff.d.eq(self.value)
        yield self.ff.clk_en.eq(1)

    def ReleaseStart(self, ctx: 'Program.Context') -> Iterable[Assign]:
        yield self.ff.clk_en.eq(0)

    def Poll(self, ctx: 'Program.Context') -> Value:
        return C(1, 1)


class Delay(Command):
    """Wait for a fixed number of cycles."""

    def __init__(self, cycles: int):
        super().__init__()
        assert cycles > 0
        self.cycles = cycles

    def Start(self, ctx: 'Program.Context') -> Iterable[Assign]:
        assert self.cycles < 2**ctx.timer.period.width
        yield ctx.timer.period.eq(self.cycles)
        yield ctx.timer.go.eq(1)

    def ReleaseStart(self, ctx: 'Program.Context') -> Iterable[Assign]:
        yield ctx.timer.go.eq(0)

    def Poll(self, ctx: 'Program.Context') -> Value:
        return ctx.timer.triggered


class WriteCommand(Command):
    """Write a command to the SSD1306 controller."""

    def __init__(self, data: ssd1306.Command):
        super().__init__()
        self.data = data

    def Start(self, ctx: 'Program.Context') -> Iterable[Assign]:
        yield from ctx.controller.WriteCommand(self.data)
        yield ctx.controller.start.eq(1)

    def ReleaseStart(self, ctx: 'Program.Context') -> Iterable[Assign]:
        yield ctx.controller.start.eq(0)

    def Poll(self, ctx: 'Program.Context') -> Value:
        return ctx.controller.done


class Program(Elaboratable):
    """Convert a list of Commands into an FSM."""

    class Context(NamedTuple):
        """Internal command execution context."""
        timer: timer_module.OneShot
        controller: ssd1306.Controller.Interface

    def __init__(self, commands: List[Command],
                 controller: ssd1306.Controller.Interface):
        super().__init__()
        assert len(commands) != 0
        for i, command in enumerate(commands):
            command.SetAddress(i)
        self.commands = commands
        self.controller = controller
        self.start = Signal(reset=0)
        self.done = Signal(reset=0)

    def elaborate(self, _: Platform) -> Module:
        m = Module()
        max_cycles = max(
            cmd.cycles for cmd in self.commands if isinstance(cmd, Delay))
        m.submodules.timer = timer = timer_module.OneShot(
            Signal(range(max_cycles)))
        ctx = Program.Context(timer, self.controller)
        m.d.sync += self.done.eq(0)  # default
        with m.FSM(reset='IDLE'):
            first = self.commands[0]
            last = self.commands[-1]
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += first.Start(ctx)
                    m.next = first.state
            for prev, next in zip(self.commands[:-1], self.commands[1:]):
                m.d.sync += prev.ReleaseStart(ctx)
                with m.State(prev.state):
                    with m.If(prev.Poll(ctx)):
                        m.d.sync += next.Start(ctx)
                        m.next = next.state
            with m.State(last.state):
                m.d.sync += last.ReleaseStart(ctx)
                with m.If(last.Poll(ctx)):
                    m.d.sync += self.done.eq(1)
                    m.next = 'IDLE'
        return m
