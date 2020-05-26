import fractions
import re
from typing import Iterable, Optional

from absl import app
from nmigen import *
from nmigen.build import *
from nmigen.lib.cdc import *

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import timer
from nmigen_nexys.core import util
from nmigen_nexys.math import delta_sigma
from nmigen_nexys.math import trig


def Parse12TETNote(text: str) -> int:
    m = re.fullmatch(r'([a-gA-G])([𝄫♭♮♯𝄪]?)([+-]?[0-9]+)', text)
    if not m:
        raise ValueError(
            f'Not a valid note: {repr(text)}. Expected C3, B♭5, A4, F𝄪7, etc.')
    m_note, m_accidental, m_octave = m.groups()
    notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    accidentals = {'𝄫': -2, '♭': -1, '♮': 0, '♯': 1, '𝄪': 2}
    note = notes[m_note.upper()]
    accidental = accidentals[m_accidental or '♮']
    octave = 1 + int(m_octave, base=10)
    midi = 12 * octave + note + accidental
    if not 0 <= midi <= 127:
        raise ValueError(f'Note out of range: {repr(text)} = {midi}')
    return midi


class BasicTonePhaseGenerator(Elaboratable):

    def __init__(self, fundamental: float, *, octaves: int = 8,
                 cents_precision: int = 5, phase_depth: int = 12):
        super().__init__()
        self.fundamental = fundamental
        self.octaves = octaves
        self.cents_precision = cents_precision
        self.phase_depth = phase_depth
        self.phase_word = Signal(phase_depth + octaves - 1)

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        # The frequency derived from delta code M is given by:
        #
        #   f(M) = M * f_clk / 2**N
        #
        # We want to choose a bit depth for M large enough to resolve the
        # fundamental frequency to within five cents (or whatever specified
        # precision), i.e.:
        #
        #   f_0 * 2**(-5/1200) ≤ M * f_clk / 2**N ≤ f_0 * 2**(5/1200)
        #
        # TODO: Might could bound the running frequency error with ΔΣ.
        f_clk = float(util.GetClockFreq(platform))
        f_0 = float(self.fundamental)
        f_min = f_0 * 2**(-5/1200)
        f_max = f_0 * 2**(5/1200)
        for N in range(self.phase_word.width, 40):
            M = int(round(f_0 * 2**N / f_clk))
            f_M = M * f_clk / 2**N
            if f_min <= f_M <= f_max:
                delta_depth = N
                delta = M
                break
        else:
            raise ValueError('Iteration safeguard exceeded')
        wheel = Signal(delta_depth)
        m.d.sync += wheel.eq(wheel + delta)
        m.d.comb += self.phase_word.eq(wheel[-self.phase_word.width:])
        return m


class TwelveTETPhaseArray(Elaboratable):

    def __init__(self, *, octaves: int = 8, cents_precision: int = 5,
                 phase_depth: int = 12):
        super().__init__()
        self.octaves = octaves
        self.cents_precision = cents_precision
        self.phase_depth = phase_depth
        A4 = Parse12TETNote('A4')
        self._tones = [
            BasicTonePhaseGenerator(
                fundamental=440 * 2**((midi - A4) / 12),
                octaves=octaves,
                cents_precision=cents_precision,
                phase_depth=phase_depth)
            for midi in range(12)
        ]
        self.tones = Array(self._tones)

    def note_phase(self, note: str) -> Value:
        # TODO: Dynamic API
        midi = Parse12TETNote(note)
        octave = midi // 12  # Note the zero-based octave instead of -1-based
        tone = midi % 12
        phase_word = self.tones[tone].phase_word
        scaled = phase_word >> (self.octaves - 1 - octave)
        return scaled[:self.phase_depth]

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        m.submodules += self._tones
        return m


class SampleLoop(Elaboratable):

    def __init__(self, tempo: int, data: Iterable[Optional[str]],
                 phi: TwelveTETPhaseArray):
        super().__init__()
        self.tempo = tempo
        self.data = data
        self.phi = phi
        self.start = Signal()
        self.playing = Signal(reset=0)
        self.phase = Signal(phi.phase_depth)

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        playing = []
        phases = []
        for datum in self.data:
            playing.append(int(datum is not None))
            phases.append(self.phi.note_phase(datum or 'A4'))
        i = Signal(range(len(self.data)), reset=0)
        bps = fractions.Fraction(self.tempo, 60)
        m.submodules.beat = beat = timer.DownTimer(
            fractions.Fraction(util.GetClockFreq(platform), bps))
        # Run through once when instructed
        m.d.sync += beat.reload.eq(0)  # Default
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += i.eq(0)
                    m.d.sync += beat.reload.eq(1)
                    m.next = 'PLAYING'
            with m.State('PLAYING'):
                m.d.comb += self.playing.eq(Array(playing)[i])
                m.d.comb += self.phase.eq(Array(phases)[i])
                with m.If(beat.triggered):
                    m.d.sync += i.eq(i + 1)
                with m.If(i + 1 == len(self.data)):
                    m.next = 'IDLE'
        return m


class SynthDemo(Elaboratable):

    def __init__(self):
        super().__init__()
        self.start = Signal()
        self.pdm_output = Signal()

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        # Sample loop
        m.submodules.phi = phi = TwelveTETPhaseArray()
        m.submodules.loop = loop = SampleLoop(360, [
            'E5',
            'F♯5',
            'G5',
            'A5',
            'F♯5',
            'F♯5',
            'D5',
            'E5',
            # -----
            'E5',
            'E5',
            None,
            None,
            None,
            None,
            None,
            None,
        ], phi)
        m.d.comb += loop.start.eq(self.start)
        # Tone generator
        m.submodules.sin = sin = trig.SineLUT(input=loop.phase,
                                              output=Signal(signed(12)))
        # Sample at 44.1 kHz
        m.submodules.sample_timer = sample_timer = timer.DownTimer(
            period=fractions.Fraction(util.GetClockFreq(platform), 44_100))
        sample = Signal(signed(16))
        with m.If(sample_timer.triggered):
            with m.If(loop.playing):
                m.d.sync += sample.eq(sin.output)
            with m.Else():
                m.d.sync += sample.eq(0)
        # Pulse-density modulated output processed by on-board LPF
        m.submodules.pdm = pdm = delta_sigma.Modulator(sample.width)
        m.d.comb += pdm.input.eq(sample)
        m.d.comb += self.pdm_output.eq(pdm.output)
        return m


class SynthDemoDriver(Elaboratable):

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        m.submodules.demo = demo = SynthDemo()
        go = platform.request('button_center')
        m.submodules.go_sync = FFSynchronizer(go, demo.start)
        audio = platform.request('audio', 0)
        m.d.comb += audio.pwm.eq(demo.pdm_output)
        m.d.comb += audio.sd.eq(0)  # No shutdown
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), SynthDemoDriver())

if __name__ == "__main__":
    app.run(main)
