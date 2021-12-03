"""Frequency modulation."""

from nmigen import *
from nmigen.build import *
from nmigen.lib.cdc import *

from nmigen_nexys.core import util
from nmigen_nexys.vendor.lattice import primitive


class ClockGenerator(Elaboratable):

    def __init__(self, domain: str):
        super().__init__()
        self.domain = domain

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        clk_freq = util.GetClockFreq(platform)
        assert clk_freq == 25_000_000  # HACK

        m.submodules.pll = pll = primitive.EHXPLLL(clki_div=1, clkfb_div=10, clkop_div=2)
        m.d.comb += [
            pll.clki.eq(ClockSignal('sync')),
            pll.clkfb.eq(pll.clkop),
            # pll.rst.eq(ResetSignal('sync')),
            pll.enclkop.eq(1),
        ]

        reset_async = Signal()
        # m.d.comb += reset_async.eq(ResetSignal('sync') | ~pll.lock)
        m.d.comb += reset_async.eq(~pll.lock)
        m.submodules.reset_sync = ResetSynchronizer(reset_async, domain=self.domain)

        m.domains += ClockDomain(self.domain)
        m.d.comb += ClockSignal(self.domain).eq(pll.clkop)

        return m


class FrequencyModulator(Elaboratable):
    """Shamelessly cribbed from https://github.com/emard/rdsfpga/blob/master/fmgen.vhd."""

    def __init__(self, *, carrier_Hz: int, pcm_depth: int, fm_domain: str):
        super().__init__()
        self.carrier_Hz = carrier_Hz
        self.pcm_depth = pcm_depth
        self.fm_domain = fm_domain
        self.pcm = Signal(signed(pcm_depth))
        self.output = Signal()

    def elaborate(self, platform: Platform) -> Module:
        m = Module()
        fm_domain_freq = 250_000_000  # HACK
        assert fm_domain_freq >= 2 * self.carrier_Hz

        # freq is the current frequency of the modulated signal
        max_freq = self.carrier_Hz + util.ShapeMax(self.pcm) * 4
        freq = Signal(unsigned(max_freq.bit_length()))
        m.d.comb += freq.eq(self.carrier_Hz + self.pcm * 4)

        # mul is the fractional part of freq/fm_domain_freq
        mul_depth = 58
        mul = Signal(unsigned(mul_depth))
        m.d.comb += mul.eq(freq * (2**mul_depth // fm_domain_freq))

        # accum is the truncated fractional part of the integral of mul
        accum_depth = 28
        incr_sync = Signal(unsigned(accum_depth))
        m.d.comb += incr_sync.eq(mul[-accum_depth:])
        incr_fm = Signal(unsigned(accum_depth))
        m.submodules.ff_sync = FFSynchronizer(incr_sync, incr_fm, o_domain=self.fm_domain)
        accum = Signal(unsigned(accum_depth))
        m.d[self.fm_domain] += accum.eq(accum + incr_fm)

        # output oscillates at approximately the frequency of the modulated
        # signal.
        m.d.comb += self.output.eq(accum[-1])

        return m


class Transmitter(Elaboratable):

    def __init__(self, pcm_depth: int = 16):
        super().__init__()
        self.pcm = Signal(pcm_depth)

    def elaborate(self, platform: Platform) -> Module:
        m = Module()

        m.submodules.clk250 = clk250 = ClockGenerator('fm')
        m.submodules.fm = fm = FrequencyModulator(carrier_Hz=107_900_000,
                                                  pcm_depth=self.pcm.width,
                                                  fm_domain=clk250.domain)
        m.d.comb += fm.pcm.eq(self.pcm)

        platform.lookup('ant', 0).attrs['DRIVE'] = 4
        m.d.comb += platform.request('ant', 0).eq(fm.output)

        return m
