"""Tests for nmigen_nexys.pmod.oled.pmod_oled."""

from typing import List, NamedTuple
import unittest

from nmigen import *
from nmigen.back.pysim import *
from nmigen.hdl.rec import *

from nmigen_nexys.core import edge
from nmigen_nexys.core import util
from nmigen_nexys.display import ssd1306
from nmigen_nexys.pmod.oled import pmod_oled
from nmigen_nexys.serial import spi
from nmigen_nexys.test import event
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


class SPIMonitor(event.Monitor):

    def __init__(self, tc: unittest.TestCase, pins: pmod_oled.PmodPins,
                 decoder: spi.BusDecoder):
        super().__init__()
        self.tc = tc
        self.pins = pins
        self.decoder = decoder

    def process(self) -> test_util.CoroutineProcess[None]:
        yield Passive()
        while True:
            events = yield from test_util.WaitSync(self.decoder.events)
            yield
            if not (events & (1 << spi.BusEvent.START)):
                continue
            dc = None
            bits = []
            while True:
                events = yield from test_util.WaitSync(self.decoder.events)
                if events & (1 << spi.BusEvent.SAMPLE):
                    bit = yield self.pins.mosi
                    bits.append(bit)
                    if len(bits) == 8:
                        dc = yield self.pins.dc
                        self.tc.assertIsNotNone(dc)
                        self.tc.assertEqual(len(bits), 8)
                        if dc:
                            yield from self.emit(DataEvent(ByteFromBits(bits)))
                        else:
                            yield from self.emit(
                                CommandEvent(ByteFromBits(bits)))
                        dc = None
                        bits = []
                if events & (1 << spi.BusEvent.STOP):
                    self.tc.assertEqual(bits, [])
                yield
            yield


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
        m.submodules.timer = timer = test_util.Timer(self, self.TIMEOUT_S)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        events = event.EventSeries(timer.cycle_counter)
        edge_monitor = event.EdgeMonitor([reset_edge, vbatc_edge, vddc_edge])
        spi_monitor = SPIMonitor(self, pins, decoder)

        def sequencer_process():
            yield sequencer.enable.eq(1)
            yield
            yield from test_util.WaitSync(
                sequencer.status == pmod_oled.PowerStatus.READY)
            yield sequencer.enable.eq(0)
            yield
            yield from test_util.WaitSync(
                sequencer.status == pmod_oled.PowerStatus.OFF)

        sim.add_sync_process(sequencer_process)
        spi_monitor.attach(sim, events)
        edge_monitor.attach(sim, events)
        sim.add_sync_process(timer.timeout_process)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=list(pins.fields.values())):
            sim.run()

        events.ShowEvents()
        expected: event.EventConstraints = [
            # Power on
            event.EdgeEvent(pins.vddc, 'fell'),
            event.MinDelay(seconds=0.1e-6),
            CommandEvent(0xAE),
            event.MinDelay(seconds=0.1e-6),
            event.EdgeEvent(pins.reset, 'rose'),
            CommandEvent(0x8D),
            CommandEvent(0x14),
            CommandEvent(0xD9),
            CommandEvent(0xF1),
            event.EdgeEvent(pins.vbatc, 'fell'),
            event.MinDelay(seconds=20.0e-6),
            CommandEvent(0xAF),
            # Power off
            CommandEvent(0xAE),
            event.EdgeEvent(pins.vbatc, 'rose'),
            event.MinDelay(seconds=20.0e-6),
            event.EdgeEvent(pins.vddc, 'rose'),
        ]
        events.ValidateConstraints(self, expected)


if __name__ == '__main__':
    unittest.main()
