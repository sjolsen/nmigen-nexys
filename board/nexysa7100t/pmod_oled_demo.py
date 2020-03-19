from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import timer as timer_module
from nmigen_nexys.core import top
from nmigen_nexys.display import ssd1306
from nmigen_nexys.pmod import pmod_oled


class Demo(Elaboratable):

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        pins = platform.request('pmod_oled', 0)
        m.submodules.sequencer = sequencer = pmod_oled.PowerSequencer(pmod_oled.PmodPins())
        m.d.comb += pins.eq(sequencer.pins)
        m.submodules.timer = timer = timer_module.OneShot(int(platform.default_clk_frequency))
        m.d.sync += timer.go.eq(0)  # default
        with m.FSM(reset='RESET'):
            with m.State('RESET'):
                m.d.sync += sequencer.enable.eq(1)
                m.next = 'WAIT_UP'
            with m.State('WAIT_UP'):
                with m.If(sequencer.status == pmod_oled.PowerStatus.READY):
                    sequencer.WriteCommand(m, ssd1306.EntireDisplayOn(True))
                    m.next = 'WAIT_FILLED'
            with m.State('WAIT_FILLED'):
                with m.If(sequencer.WaitDone(m)):
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
