import fractions
import re
from typing import Iterable, Optional, Tuple

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


class AudioPhaseGenerator(Elaboratable):

    # log2 (f_clk / (f_floor * (2^((5/100) / 12) - 1))) ~= 30.7
    DELTA_DEPTH = 31

    def __init__(self, phase_depth: int = 12):
        super().__init__()
        assert phase_depth <= self.DELTA_DEPTH
        self.note = Signal(self.DELTA_DEPTH)
        self.octave = Signal(4)
        self.phase_word = Signal(phase_depth)
        self.update = Signal(reset=0)

    @classmethod
    def CanonicalDelta(cls, text: str, platform: Optional[Platform]) -> int:
        m = re.fullmatch(r'([a-gA-G])([𝄫♭♮♯𝄪]?)', text)
        assert m
        note, accidental = m.groups()
        notes = {'A': 0, 'B': 2, 'C': -9, 'D': -7, 'E': -5, 'F': -4, 'G': -2}
        accidentals = {'𝄫': -2, '♭': -1, '♮': 0, '♯': 1, '𝄪': 2}
        semitones = notes[note.upper()] + accidentals[accidental or '♮']
        octave = 15
        A4 = 440
        frequency = A4 * 2**(octave - 4 + semitones / 12)
        return int(round(frequency * 2**cls.DELTA_DEPTH / util.GetClockFreq(platform)))

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        delta_word = Signal(self.DELTA_DEPTH)
        wheel = Signal.like(delta_word)
        new_delta = Signal.like(delta_word)
        m.d.comb += new_delta.eq(self.note >> (15 - self.octave))
        with m.If(self.update & (new_delta != delta_word)):
            m.d.sync += delta_word.eq(new_delta)
            m.d.sync += wheel.eq(0)
        with m.Else():
            m.d.sync += wheel.eq(wheel + delta_word)
        m.d.comb += self.phase_word.eq(wheel[-self.phase_word.width:])
        return m


class SampleLoop(Elaboratable):

    def __init__(self, tempo: int, data: Iterable[Optional[Tuple[str, int]]]):
        super().__init__()
        self.tempo = tempo
        self.data = data
        self.start = Signal()
        self.playing = Signal()
        self.note = Signal(AudioPhaseGenerator.DELTA_DEPTH)
        self.octave = Signal(4)
        self.tick = Signal()
        self.volume = Signal()

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        notes = []
        octaves = []
        volumes = []
        for datum in self.data:
            if datum is None:
                notes.append(AudioPhaseGenerator.CanonicalDelta('A', platform))
                octaves.append(4)
                volumes.append(0)
            else:
                note, octave = datum
                notes.append(AudioPhaseGenerator.CanonicalDelta(note, platform))
                octaves.append(octave)
                volumes.append(1)
        i = Signal(range(len(self.data)), reset=0)
        m.d.comb += self.note.eq(Array(notes)[i])
        m.d.comb += self.octave.eq(Array(octaves)[i])
        m.d.comb += self.volume.eq(Array(volumes)[i])
        bps = fractions.Fraction(self.tempo, 60)
        m.submodules.beat = beat = timer.DownTimer(fractions.Fraction(util.GetClockFreq(platform), bps))
        # Run through once when instructed
        m.d.sync += beat.reload.eq(0)  # Default
        m.d.sync += self.tick.eq(0)  # Default
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(self.start):
                    m.d.sync += i.eq(0)
                    m.d.sync += beat.reload.eq(1)
                    m.d.sync += self.tick.eq(1)  # Trigger first sample immediately
                    m.next = 'PLAYING'
            with m.State('PLAYING'):
                m.d.comb += self.playing.eq(1)
                with m.If(beat.triggered):
                    m.d.sync += i.eq(i + 1)
                    m.d.sync += self.tick.eq(1)  # Delay one cycle to pick up array updates
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
        # Tone generator
        m.submodules.phi = phi = AudioPhaseGenerator()
        m.submodules.sin = sin = trig.SineLUT(Signal.like(phi.phase_word), Signal(signed(12)))
        m.d.comb += sin.input.eq(phi.phase_word)
        # Sample loop
        m.submodules.loop = loop = SampleLoop(360, [
            ('E', 5),
            ('F♯', 5),
            ('G', 5),
            ('A', 5),
            ('F♯', 5),
            ('F♯', 5),
            ('D', 5),
            ('E', 5),
            # -----
            ('E', 5),
            ('E', 5),
            None,
            None,
            None,
            None,
            None,
            None,
        ])
        m.d.comb += loop.start.eq(self.start)
        m.d.comb += phi.note.eq(loop.note)
        m.d.comb += phi.octave.eq(loop.octave)
        m.d.comb += phi.update.eq(loop.tick)
        # Sample at 44.1 kHz
        m.submodules.sample_timer = sample_timer = timer.DownTimer(
            period=fractions.Fraction(util.GetClockFreq(platform), 44_100))
        sample = Signal(signed(16))
        with m.If(sample_timer.triggered):
            with m.If(loop.volume & loop.playing):
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
