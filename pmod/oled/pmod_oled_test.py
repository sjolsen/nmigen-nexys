"""Tests for nmigen_nexys.pmod.oled.pmod_oled."""

from typing import List, NamedTuple, Tuple, Union
import unittest

from nmigen import *
from nmigen.back.pysim import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import edge
from nmigen_nexys.core import util
from nmigen_nexys.display import ssd1306
from nmigen_nexys.pmod.oled import pmod_oled
from nmigen_nexys.serial import spi
from nmigen_nexys.test import test_util


def ByteFromBits(bits: List[int]) -> int:
    """Big-endian bits-to-int convertion."""
    assert len(bits) == 8
    assert all(0 <= b <= 1 for b in bits)
    return sum(b * 2**i for i, b in enumerate(reversed(bits)))


class CommandEvent(NamedTuple):
    """Simulation event: command sent to controller."""
    byte: int


class DataEvent(NamedTuple):
    """Simulation event: data sent to controller."""
    byte: int


class EdgeEvent(NamedTuple):
    """Simulation event: GPIO toggled."""
    signal: str
    direction: str  # TODO(python-3.8): Literal['rose', 'fell']


Event = Union[CommandEvent, DataEvent, EdgeEvent]


class PowerSequenceTest(unittest.TestCase):
    """Simulate and validate the power-sequencing logic."""

    TIMEOUT_S = 50e-6

    def test_up_down(self):
        m = Module()
        pins = pmod_oled.PmodPins()
        m.submodules.controller = controller = ssd1306.Controller(
            pins.ControllerBus(), max_data_bytes=0)
        m.submodules.sequencer = sequencer = pmod_oled.PowerSequencer(
            pins, controller.interface, sim_logic_wait_us=0.1,
            sim_vcc_wait_us=20)
        m.submodules.decoder = decoder = spi.BusDecoder(
            controller.bus.SPIBus(), polarity=C(0, 1), phase=C(0, 1))
        m.submodules.reset_edge = reset_edge = edge.Detector(pins.reset)
        m.submodules.vbatc_edge = vbatc_edge = edge.Detector(pins.vbatc)
        m.submodules.vddc_edge = vddc_edge = edge.Detector(pins.vddc)
        timestamp = Signal(
            range(int(self.TIMEOUT_S * util.SIMULATION_CLOCK_FREQUENCY)),
            reset=0)
        m.d.sync += timestamp.eq(timestamp + 1)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        sim_events: List[Tuple[int, Event]] = []

        def sequencer_process():
            yield sequencer.enable.eq(1)
            yield
            yield from test_util.WaitSync(
                sequencer.status == pmod_oled.PowerStatus.READY)
            yield sequencer.enable.eq(0)
            yield
            yield from test_util.WaitSync(
                sequencer.status == pmod_oled.PowerStatus.OFF)

        def spi_monitor():
            yield Passive()
            while True:
                events = yield from test_util.WaitSync(decoder.events)
                yield
                if not (events & (1 << spi.BusEvent.START)):
                    continue
                dc = None
                bits = []
                while True:
                    events = yield from test_util.WaitSync(decoder.events)
                    if events & (1 << spi.BusEvent.SAMPLE):
                        bit = yield pins.mosi
                        bits.append(bit)
                        if len(bits) == 8:
                            now = yield timestamp
                            dc = yield pins.dc
                            self.assertIsNotNone(dc)
                            self.assertEqual(len(bits), 8)
                            if dc:
                                sim_events.append(
                                    (now, DataEvent(ByteFromBits(bits))))
                            else:
                                sim_events.append(
                                    (now, CommandEvent(ByteFromBits(bits))))
                            dc = None
                            bits = []
                    if events & (1 << spi.BusEvent.STOP):
                        self.assertEqual(bits, [])
                    yield
                yield

        def edge_monitor():
            yield Passive()
            while True:
                yield
                for detector in [reset_edge, vbatc_edge, vddc_edge]:
                    now = yield timestamp
                    rose = yield detector.rose
                    fell = yield detector.fell
                    if rose:
                        sim_events.append(
                            (now, EdgeEvent(detector.input.name, 'rose')))
                    if fell:
                        sim_events.append(
                            (now, EdgeEvent(detector.input.name, 'fell')))

        def timeout():
            yield Passive()
            yield Delay(self.TIMEOUT_S)
            self.fail('Test timed out after {self.TIMEOUT_S} s')

        sim.add_sync_process(sequencer_process)
        sim.add_sync_process(spi_monitor)
        sim.add_sync_process(edge_monitor)
        sim.add_sync_process(timeout)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=list(pins.fields.values())):
            sim.run()

        if not sim_events:
            self.fail('No simulation events captured')
        dbg_table = []
        for (ts, e), (pts, prev) in zip(sim_events, [(None, None)] + sim_events[:-1]):
            diff = f'({ts - pts:+})' if prev else ' '
            dbg_table.append((str(ts), diff, repr(e)))
        widths = [max(len(row[col]) for row in dbg_table) for col in range(2)]
        dbg_out = ['Simulation events:']
        for ts, diff, disp in dbg_table:
            dbg_out.append(f'  {ts:>{widths[0]}} {diff:>{widths[1]}} {disp}')
        print('\n'.join(dbg_out))

        expected: Union[Event, float] = [
            # Power on
            EdgeEvent(pins.vddc.name, 'fell'),
            0.1,
            CommandEvent(0xAE),
            0.1,
            EdgeEvent(pins.reset.name, 'rose'),
            CommandEvent(0x8D),
            CommandEvent(0x14),
            CommandEvent(0xD9),
            CommandEvent(0xF1),
            EdgeEvent(pins.vbatc.name, 'fell'),
            20.0,
            CommandEvent(0xAF),
            # Power off
            CommandEvent(0xAE),
            EdgeEvent(pins.vbatc.name, 'rose'),
            20.0,
            EdgeEvent(pins.vddc.name, 'rose'),
        ]
        last_ts = 0.0
        min_delta = None
        actual_iter = iter(sim_events)
        for expectation in expected:
            if isinstance(expectation, float):
                min_delta = expectation
                continue
            else:
                min_delta = 0.0
            ts, this = next(actual_iter)
            self.assertEqual(this, expectation)
            self.assertGreaterEqual(ts - last_ts, min_delta)
            last_ts = ts


if __name__ == '__main__':
    unittest.main()
