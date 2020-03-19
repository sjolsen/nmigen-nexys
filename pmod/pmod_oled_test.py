import unittest

from nmigen import *
from nmigen.back.pysim import *
from nmigen.hdl.rec import *

from nmigen_nexys.pmod import pmod_oled
from nmigen_nexys.test import util


class MockResource(Record):

    LAYOUT = Layout([
        ('cs', 1),
        ('mosi', 1),
        ('sclk', 1),
        ('dc', 1),
        ('reset', 1),
        ('vbatc', 1),
        ('vddc', 1),
    ])

    def __init__(self):
        super().__init__(self.LAYOUT, fields={
            name: Signal(shape, name=name)
            for name, (shape, _) in self.LAYOUT.fields.items()
        })


class PowerSequenceTest(unittest.TestCase):

    def test_up_down(self):
        m = Module()
        pins = MockResource()
        m.submodules.sequencer = sequencer = pmod_oled.PowerSequencer(
            pins, sim_clk_freq=100_000_000, sim_vcc_wait_us=20)
        sim = Simulator(m)
        sim.add_clock(1e-8)  # 100 MHz

        def sequencer_process():
            yield sequencer.enable.eq(1)
            yield
            yield from util.WaitDone(
                sequencer.status == pmod_oled.PowerStatus.READY)
            yield sequencer.enable.eq(0)
            yield
            yield from util.WaitDone(
                sequencer.status == pmod_oled.PowerStatus.OFF)

        def timeout():
            yield Passive()
            yield Delay(50e-6)
            self.fail('Test timed out after 50 us')

        sim.add_sync_process(sequencer_process)
        sim.add_sync_process(timeout)
        test_dir = util.BazelTestOutput(self.id())
        os.makedirs(test_dir, exist_ok=True)
        with sim.write_vcd(os.path.join(test_dir, "test.vcd"),
                           os.path.join(test_dir, "test.gtkw"),
                           traces=list(pins.fields.values())):
            sim.run()


if __name__ == '__main__':
    unittest.main()
