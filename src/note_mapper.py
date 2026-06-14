"""Map frequencies to musical note names (Vietnamese + English)."""

import numpy as np

# 12 pitch classes, index 0 = C
_VI_NAMES = [
    'Đô', 'Đô#/Rê♭', 'Rê', 'Rê#/Mi♭', 'Mi',
    'Fa', 'Fa#/Sol♭', 'Sol', 'Sol#/La♭', 'La', 'La#/Si♭', 'Si'
]
_EN_NAMES = [
    'C', 'C#/Db', 'D', 'D#/Eb', 'E',
    'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B'
]
_SIMPLE_VI = ['Đô', 'Đô#', 'Rê', 'Rê#', 'Mi', 'Fa', 'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si']
_SIMPLE_EN = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def freq_to_midi(freq: float) -> float | None:
    """Convert frequency in Hz to MIDI note number (float)."""
    if freq is None or freq <= 0:
        return None
    return 69.0 + 12.0 * np.log2(freq / 440.0)


def midi_to_note_parts(midi_num: float) -> tuple[str, str, str, int]:
    """Return (vi_name, en_name, en_simple, octave) from a MIDI note number."""
    midi_int = int(round(midi_num))
    pitch_class = midi_int % 12
    octave = (midi_int // 12) - 1
    return _VI_NAMES[pitch_class], _EN_NAMES[pitch_class], _SIMPLE_EN[pitch_class], octave


def freq_to_note(freq: float) -> dict | None:
    """Convert frequency (Hz) to a full note info dict."""
    midi = freq_to_midi(freq)
    if midi is None:
        return None
    vi_name, en_name, en_simple, octave = midi_to_note_parts(midi)
    cents_off = (midi - round(midi)) * 100
    return {
        'freq_hz': round(freq, 2),
        'midi': round(midi, 2),
        'vi_name': vi_name,
        'en_name': en_name,
        'en_simple': en_simple,
        'octave': octave,
        'label': f'{vi_name}{octave}',
        'label_en': f'{en_simple}{octave}',
        'cents_off': round(cents_off, 1),
    }


def midi_range_for_piano() -> list[tuple[int, str, str]]:
    """Return list of (midi_num, vi_name, en_name) for the standard piano range."""
    notes = []
    for midi in range(21, 109):
        pc = midi % 12
        oct_ = (midi // 12) - 1
        notes.append((midi, f'{_SIMPLE_VI[pc]}{oct_}', f'{_SIMPLE_EN[pc]}{oct_}'))
    return notes
