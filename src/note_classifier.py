"""Classify note duration into musical note types (whole, half, quarter, etc.)."""

import numpy as np  # noqa: F401 – used for isfinite

# (beat_value, vi_name, en_name, unicode_symbol)
NOTE_TYPES = [
    (8.0,   'Nốt tròn đôi',   'double-whole',    '𝅜'),
    (4.0,   'Nốt tròn',       'whole',            '𝅝'),
    (3.0,   'Trắng chấm',     'dotted-half',      '𝅗𝅥.'),
    (2.0,   'Nốt trắng',      'half',             '𝅗𝅥'),
    (1.5,   'Đen chấm',       'dotted-quarter',   '♩.'),
    (1.0,   'Nốt đen',        'quarter',          '♩'),
    (0.75,  'Móc đơn chấm',   'dotted-eighth',    '♪.'),
    (0.5,   'Móc đơn',        'eighth',           '♪'),
    (0.375, 'Móc kép chấm',   'dotted-sixteenth', '𝅘𝅥𝅯.'),
    (0.25,  'Móc kép',        'sixteenth',        '𝅘𝅥𝅯'),
    (0.125, 'Móc ba',         'thirty-second',    '𝅘𝅥𝅰'),
]


def beats_to_note_type(beats: float, tolerance: float = 0.25) -> dict:
    """Classify a note duration (in beats) to a note type."""
    best = None
    best_ratio = float('inf')
    for beat_val, vi_name, en_name, symbol in NOTE_TYPES:
        ratio = abs(beats - beat_val) / beat_val
        if ratio < best_ratio:
            best_ratio = ratio
            best = (beat_val, vi_name, en_name, symbol)

    beat_val, vi_name, en_name, symbol = best
    confidence = max(0.0, 1.0 - best_ratio / tolerance) if best_ratio < tolerance else 0.0
    return {
        'beat_value': beat_val,
        'vi_name': vi_name,
        'en_name': en_name,
        'symbol': symbol,
        'confidence': round(min(confidence, 1.0), 2),
        'beats_detected': round(beats, 3),
    }


def duration_to_note_type(duration_sec: float, tempo_bpm: float) -> dict:
    """Convert note duration in seconds to note type given tempo in BPM."""
    if not np.isfinite(tempo_bpm) or tempo_bpm < 20:
        tempo_bpm = 120.0
    beat_duration = 60.0 / tempo_bpm
    beats = duration_sec / beat_duration
    result = beats_to_note_type(beats)
    result['duration_sec'] = round(duration_sec, 3)
    result['tempo_bpm'] = round(tempo_bpm, 1)
    return result
