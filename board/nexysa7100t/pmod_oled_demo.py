from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import top
from nmigen_nexys.core import util
from nmigen_nexys.display import ssd1306
from nmigen_nexys.pmod import pmod_oled


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        pins = pmod_oled.PmodPins()
        m.d.comb += platform.request('pmod_oled', 0).eq(pins)
        m.submodules.controller = controller = ssd1306.SSD1306(pins.ControllerBus(), max_data_bytes=0)
        ifaces = [ssd1306.SSD1306.Interface(controller.interface.max_bits) for _ in range(2)]
        select = Signal(reset=0)
        m.d.comb += util.Multiplex(select, controller.interface, ifaces)
        m.submodules.sequencer = sequencer = pmod_oled.PowerSequencer(pins, ifaces[0])
        m.submodules.timer = timer = timer_module.OneShot(int(platform.default_clk_frequency))
        m.d.sync += timer.go.eq(0)  # default
        m.d.sync += ifaces[1].start.eq(0)  # default
        with m.FSM(reset='RESET'):
            with m.State('RESET'):
                m.d.sync += sequencer.enable.eq(1)
                m.next = 'WAIT_UP'
            with m.State('WAIT_UP'):
                with m.If(sequencer.status == pmod_oled.PowerStatus.READY):
                    m.d.sync += select.eq(1)
                    m.d.sync += ifaces[1].WriteCommand(ssd1306.EntireDisplayOn(True))
                    m.d.sync += ifaces[1].start.eq(1)
                    m.next = 'WAIT_FILLED'
            with m.State('WAIT_FILLED'):
                with m.If(ifaces[1].done):
                    m.d.sync += select.eq(0)
                    m.d.sync += timer.go.eq(1)
                    m.next = 'KEEP_ON'
            with m.State('KEEP_ON'):
                with m.If(timer.triggered):
                    m.d.sync += sequencer.enable.eq(0)
                    m.next = 'OFF'
            with m.State('OFF'):
                pass

        leds = Cat(*[platform.request('led', i) for i in range(4)])
        m.d.comb += leds.eq(1 << sequencer.status)
        return m


if __name__ == "__main__":
    platform = nexysa7100t.NexysA7100TPlatform()
    platform.add_resources([
        pmod_oled.PmodOLEDResource(0, conn=('pmod', 2)),
    ])
    top.main(platform, Demo())
