import fractions
import re
from typing import Iterable, Optional

from absl import app
from nmigen import *
from nmigen.build import *
from nmigen.hdl.ast import Statement
from nmigen.lib.cdc import FFSynchronizer

from nmigen_nexys.bazel import top
from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.core import shift_register
from nmigen_nexys.core import timer
from nmigen_nexys.core import util
from nmigen_nexys.math import delta_sigma
from nmigen_nexys.math import trig
from nmigen_nexys.serial import uart


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
    octave = 1 + int(m_octave, base=10)  # Note the zero-based octave instead of -1-based
    midi = 12 * octave + note + accidental
    if not 0 <= midi <= 127:
        raise ValueError(f'Note out of range: {repr(text)} = {midi}')
    return midi


class BasicTonePhaseGenerator(Elaboratable):

    def __init__(self, fundamental: float, *, octaves: int = 16,
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

    def note_phase(self, tone: Value, octave: Value) -> Value:
        phase_word = self.tones[tone].phase_word
        scaled = phase_word >> (self.octaves - 1 - octave)
        return scaled[:self.phase_depth]

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        m.submodules += self._tones
        return m


class SampleLoop(Elaboratable):

    def __init__(self, tempo: int, data: Iterable[Optional[str]],
                 octaves: int):
        super().__init__()
        self.tempo = tempo
        self.data = data
        self.octaves = octaves
        self.start = Signal()
        self.notes = Signal(octaves * 12)
        self.playing = Signal()

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        sequence = []
        for datum in self.data:
            notes = Signal.like(self.notes)
            for note in datum:
                m.d.comb += notes[Parse12TETNote(note)].eq(1)
            sequence.append(notes)
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
                m.d.comb += self.playing.eq(1)
                m.d.comb += self.notes.eq(Array(sequence)[i])
                with m.If(beat.triggered):
                    m.d.sync += i.eq(i + 1)
                with m.If(i + 1 == len(self.data)):
                    m.next = 'IDLE'
        return m


# TODO: Better
def SatAdd(m: Module, lhs: Signal, rhs: Value) -> Statement:
    plus = Signal(
        Shape(signed=lhs.signed, width=lhs.width + 1),
        name=f'{lhs.name}_plus_{rhs.name}')
    m.d.comb += plus.eq(lhs + rhs)
    return lhs.eq(
        Mux(
            plus > util.ShapeMax(lhs.shape()),
            util.ShapeMax(lhs.shape()),
            Mux(
                plus < util.ShapeMin(lhs.shape()),
                util.ShapeMin(lhs.shape()),
                plus)))


class BasicMIDISink(Elaboratable):

    def __init__(self, *, baud_rate: int = 31_250):
        super().__init__()
        self.baud_rate = baud_rate
        self.rx = Signal()
        self.channels = Array([Signal(128) for _ in range(16)])

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        m.submodules.rx = rx = uart.Receive(self.baud_rate)
        m.d.comb += rx.input.eq(self.rx)
        cmd = Signal(8)
        channel = self.channels[cmd[:4]]
        m.submodules.data = data = shift_register.ArrayUp(width=7, count=2)
        data_remaining = Signal(range(data.count + 1))
        m.d.comb += data.word_in.eq(rx.data[:7])
        with m.If(rx.done):
            with m.Switch(rx.data):
                with m.Case('1000----'):
                    # Note off
                    m.d.sync += cmd.eq(rx.data)
                    m.d.sync += data_remaining.eq(2)
                with m.Case('1001----'):
                    # Note on
                    m.d.sync += cmd.eq(rx.data)
                    m.d.sync += data_remaining.eq(2)
                with m.Case('0-------'):
                    m.d.comb += data.shift.eq(1)
                    with m.If(data_remaining):
                        m.d.sync += data_remaining.eq(data_remaining - 1)
        with m.If(data_remaining == 0):
            with m.Switch(cmd):
                with m.Case('1000----'):
                    # Note off
                    note = data.words_out[1]
                    velocity = data.words_out[0]
                    m.d.sync += channel.eq(channel & ~(1 << note))
                    m.d.sync += cmd.eq(0)
                with m.Case('1001----'):
                    # Note on
                    note = data.words_out[1]
                    velocity = data.words_out[0]
                    m.d.sync += channel.eq(channel | (1 << note))
                    m.d.sync += cmd.eq(0)
        return m


class Mixer(Elaboratable):

    def __init__(self, notes: Value, phi: TwelveTETPhaseArray,
                 bit_depth: int = 16):
        super().__init__()
        self.notes = notes
        self.phi = phi
        self.bit_depth = bit_depth
        self.sample = Signal(bit_depth)
        self.update = Signal()

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        # Tone generator
        m.submodules.sin = sin = trig.SineLUT(
            input=Signal(self.phi.phase_depth), output=Signal(signed(12)))
        # Sample at 44.1 kHz
        m.submodules.sample_timer = sample_timer = timer.DownTimer(
            period=fractions.Fraction(util.GetClockFreq(platform), 44_100))
        sample = Signal.like(self.sample)
        notes = Signal.like(self.notes)
        tone = Signal(range(12))
        octave = Signal(range(self.phi.octaves))
        m.d.sync += self.update.eq(0)  # Default
        with m.FSM(reset='IDLE'):
            with m.State('IDLE'):
                with m.If(sample_timer.triggered):
                    with m.If(self.notes):
                        m.d.sync += sample.eq(0)
                        m.d.sync += notes.eq(self.notes)
                        m.d.sync += tone.eq(0)
                        m.d.sync += octave.eq(0)
                        m.next = 'SAMPLING'
                    with m.Else():
                        m.d.sync += self.sample.eq(0)
                        m.d.sync += self.update.eq(1)
            with m.State('SAMPLING'):
                m.d.comb += sin.input.eq(self.phi.note_phase(tone, octave))
                with m.If(notes[0]):
                    # m.d.sync += SatAdd(m, sample, sin.output)
                    m.d.sync += sample.eq(sample + sin.output)  # TODO: Saturating addition
                m.d.sync += notes.eq(notes >> 1)
                with m.If(tone + 1 == 12):
                    m.d.sync += tone.eq(0)
                    m.d.sync += octave.eq(octave + 1)
                with m.Else():
                    m.d.sync += tone.eq(tone + 1)
                with m.If(~(notes >> 1).any()):
                    m.next = 'UPDATE'
            with m.State('UPDATE'):
                m.d.sync += self.sample.eq(sample)
                m.d.sync += self.update.eq(1)
                m.next = 'IDLE'
        return m


class SynthDemo(Elaboratable):

    def __init__(self):
        super().__init__()
        self.rx = Signal()
        self.start = Signal()
        self.pdm_output = Signal()
        self.channels = Signal(16)

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        m.submodules.phi = phi = TwelveTETPhaseArray()
        # Sample loop
        m.submodules.loop = loop = SampleLoop(360, [
            ['E4', 'A4', 'D5'],
            ['E5'],
            ['F5'],
            ['G5'],
            ['D4', 'G4', 'C5', 'E5'],
            ['E5'],
            ['C5'],
            ['B♭3', 'C4', 'F4', 'D5'],
            # -----
            ['B♭3', 'C4', 'F4', 'D5'],
            ['B♭3', 'C4', 'F4', 'D5'],
            [],
            [],
            [],
            [],
            [],
            [],
        ], phi.octaves)
        m.d.comb += loop.start.eq(self.start)
        # MIDI sink
        m.submodules.midi = midi = BasicMIDISink(baud_rate=115_200)
        m.d.comb += midi.rx.eq(self.rx)
        midi_notes = Signal.like(midi.channels[0])
        for i in range(midi_notes.width):
            m.d.comb += midi_notes[i].eq(
                util.Any(c[i] for c in midi.channels))
            m.d.comb += self.channels.eq(
                Cat(*[c.any() for c in midi.channels]))
        # Mixer
        notes = Signal(12 * phi.octaves)
        m.d.comb += notes.eq(Mux(loop.playing, loop.notes, midi_notes))
        m.submodules.mixer = mixer = Mixer(notes, phi)
        # Pulse-density modulated output processed by on-board LPF
        m.submodules.pdm = pdm = delta_sigma.Modulator(mixer.sample.width)
        m.d.comb += pdm.input.eq(mixer.sample)
        m.d.comb += self.pdm_output.eq(pdm.output)
        return m


class SynthDemoDriver(Elaboratable):

    def elaborate(self, platform: Optional[Platform]) -> Module:
        m = Module()
        m.submodules.demo = demo = SynthDemo()
        go = platform.request('button_center')
        m.submodules.go_sync = FFSynchronizer(go, demo.start)
        rx = platform.request('uart', 0).rx
        m.submodules.rx_sync = FFSynchronizer(rx, demo.rx)
        audio = platform.request('audio', 0)
        m.d.comb += audio.pwm.eq(demo.pdm_output)
        m.d.comb += audio.sd.eq(0)  # No shutdown
        leds = Cat(*[platform.request('led', i) for i in range(16)])
        m.d.comb += leds.eq(demo.channels)
        return m


def main(_):
    top.build(nexysa7100t.NexysA7100TPlatform(), SynthDemoDriver())

if __name__ == "__main__":
    app.run(main)
