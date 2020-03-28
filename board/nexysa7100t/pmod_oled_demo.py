"""Demo for https://store.digilentinc.com/pmod-oled-128-x-32-pixel-monochromatic-oled-display/."""

from absl import app
from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import shift_register
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import top
from nmigen_nexys.core import util
from nmigen_nexys.display import ssd1306
from nmigen_nexys.math import lfsr as lfsr_module
from nmigen_nexys.pmod.oled import pmod_oled


class Demo(Elaboratable):
    """Demo for the Digilent Pmod OLED.

    This demo assumes the module is plugged into JC. It displays pseudo-random
    data, similar to the noise you'd see on an old NTSC television.
    """

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        m.submodules.lfsr = lfsr = lfsr_module.Fibonacci(
            polynomial=[24, 23, 22, 17, 0], seed=0x123456)
        m.submodules.data = data = shift_register.Up(64)
        m.d.comb += data.bit_in.eq(lfsr.output)
        m.d.comb += data.shift.eq(1)

        pins = pmod_oled.PmodPins()
        m.d.comb += platform.request('pmod_oled', 0).eq(pins)
        m.submodules.controller = controller = ssd1306.Controller(
            pins.ControllerBus(), max_data_bytes=8)
        ifaces = [
            ssd1306.Controller.Interface(controller.interface.max_bits)
            for _ in range(2)
        ]
        select = Signal(reset=0)
        m.d.comb += util.Multiplex(select, controller.interface, ifaces)
        m.submodules.sequencer = sequencer = pmod_oled.PowerSequencer(
            pins, ifaces[0])
        m.submodules.timer = timer = timer_module.UpTimer(
            util.GetClockFreq(platform) // 10)
        m.d.sync += ifaces[1].start.eq(0)  # default
        with m.FSM(reset='RESET'):
            with m.State('RESET'):
                with m.If(timer.triggered):
                    m.next = 'START'
            with m.State('START'):
                m.d.sync += sequencer.enable.eq(1)
                m.next = 'WAIT_UP'
            with m.State('WAIT_UP'):
                with m.If(sequencer.status == pmod_oled.PowerStatus.READY):
                    m.d.sync += select.eq(1)
                    m.d.sync += ifaces[1].WriteCommand(
                        ssd1306.SetMemoryAddressingMode(
                            ssd1306.AddressingMode.VERTICAL))
                    m.d.sync += ifaces[1].start.eq(1)
                    m.next = 'DRAW'
            with m.State('DRAW'):
                with m.If(ifaces[1].done):
                    m.d.sync += ifaces[1].WriteData(data.word_out)
                    m.d.sync += ifaces[1].start.eq(1)

        leds = Cat(*[platform.request('led', i) for i in range(4)])
        m.d.comb += leds.eq(1 << sequencer.status)
        return m


def main(_):
    platform = nexysa7100t.NexysA7100TPlatform()
    platform.add_resources([
        pmod_oled.PmodOLEDResource(0, conn=('pmod', 2)),
    ])
    top.build(platform, Demo())

if __name__ == "__main__":
    app.run(main)
