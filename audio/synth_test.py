import os
import unittest

import mido
from nmigen import *
from nmigen.back.pysim import *

from nmigen_nexys.audio import synth
from nmigen_nexys.core import util
from nmigen_nexys.serial import uart
from nmigen_nexys.test import test_util


class BasicMIDISinkTest(unittest.TestCase):

    def test_note_on_off(self):
        m = Module()
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.submodules.midi = midi = synth.BasicMIDISink(
            baud_rate=12_000_000)
        m.d.comb += midi.rx.eq(tx.output)
        m.submodules.timer = timer = test_util.Timer(self, timeout_s=10e-6)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def send(msg: mido.Message):
            for datum in msg.bytes():
                yield tx.data.eq(datum)
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield from test_util.WaitSync(tx.done)

        def driver():
            yield Passive()
            yield from send(mido.Message('note_on', note=69))
            yield from send(mido.Message('note_off', note=69))

        def check():
            yield Active()
            yield from test_util.WaitSync(
                midi.channels[0][synth.Parse12TETNote('A4')])
            yield from test_util.WaitSync(
                ~midi.channels[0][synth.Parse12TETNote('A4')])

        sim.add_sync_process(driver)
        sim.add_sync_process(check)
        sim.add_sync_process(timer.timeout_process)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[tx.output, midi.channels[0]]):
            sim.run()

    def test_note_on_0(self):
        m = Module()
        m.submodules.tx = tx = uart.Transmit(12_000_000)
        m.submodules.midi = midi = synth.BasicMIDISink(
            baud_rate=12_000_000)
        m.d.comb += midi.rx.eq(tx.output)
        m.submodules.timer = timer = test_util.Timer(self, timeout_s=10e-6)
        sim = Simulator(m)
        sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

        def send(msg: mido.Message):
            for datum in msg.bytes():
                yield tx.data.eq(datum)
                yield tx.start.eq(1)
                yield
                yield tx.start.eq(0)
                yield from test_util.WaitSync(tx.done)

        def driver():
            yield Passive()
            yield from send(mido.Message('note_on', note=69))
            yield from send(mido.Message('note_on', note=69, velocity=0))

        def check():
            yield Active()
            yield from test_util.WaitSync(
                midi.channels[0][synth.Parse12TETNote('A4')])
            yield from test_util.WaitSync(
                ~midi.channels[0][synth.Parse12TETNote('A4')])

        sim.add_sync_process(driver)
        sim.add_sync_process(check)
        sim.add_sync_process(timer.timeout_process)
        test_dir = test_util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=[tx.output, midi.channels[0]]):
            sim.run()


# class DemoTest(unittest.TestCase):

#     def test_demo(self):
#         m = Module()
#         m.submodules.demo = demo = synth.Demo()
#         m.d.comb += demo.start.eq(1)
#         sim = Simulator(m)
#         sim.add_clock(1.0 / util.SIMULATION_CLOCK_FREQUENCY)

#         test_dir = test_util.BazelTestOutput(self.id())
#         os.makedirs(test_dir, exist_ok=True)
#         with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
#                            os.path.join(test_dir, "test.gtkw"),
#                            traces=[demo.pdm_output]):
#             sim.run_until(250e-6, run_passive=True)


if __name__ == '__main__':
    unittest.main()
