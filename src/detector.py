"""Core pipeline: load audio → detect onsets → detect pitch → classify notes."""

import numpy as np

from src.audio_loader import load_audio, normalize_audio, trim_silence
from src.onset_detector import detect_onsets, estimate_tempo, build_note_segments
from src.pitch_detector import detect_pitch_all_segments, is_silence
from src.note_mapper import freq_to_note, freq_to_midi
from src.note_classifier import duration_to_note_type


def detect_notes(
    audio_path: str,
    onset_delta: float = 0.07,
    wait_ms: float = 80,
    min_duration: float = 0.05,
    trim: bool = True,
) -> dict:
    """Full pipeline: audio file → list of detected notes.

    Returns a dict with:
      - notes: list of note dicts
      - tempo_bpm: estimated tempo
      - total_duration: audio length in seconds
      - sr: sample rate
    """
    print(f"  Đang tải: {audio_path}")
    y, sr = load_audio(audio_path)
    y = normalize_audio(y)
    if trim:
        y = trim_silence(y, sr)
    total_duration = len(y) / sr
    print(f"  Thời lượng: {total_duration:.2f}s  |  SR: {sr} Hz")

    print("  Phát hiện tempo và nhịp...")
    tempo, beat_times = estimate_tempo(y, sr)
    print(f"  Tempo ước tính: {tempo:.1f} BPM")

    print("  Phát hiện điểm bắt đầu nốt (onsets)...")
    onset_times = detect_onsets(y, sr, delta=onset_delta, wait_ms=wait_ms)
    print(f"  Tìm thấy {len(onset_times)} điểm onset")

    segments = build_note_segments(onset_times, total_duration, min_duration=min_duration)
    print(f"  Phân đoạn thành {len(segments)} vùng nốt")

    print("  Phát hiện cao độ từng nốt (pYIN)...")
    pitches = detect_pitch_all_segments(y, sr, segments)

    notes = []
    for i, ((start, end), pitch) in enumerate(zip(segments, pitches)):
        duration = end - start
        seg_audio = y[int(start * sr):int(end * sr)]
        silence = is_silence(seg_audio)

        if silence or pitch is None:
            notes.append({
                'index': i + 1,
                'start': round(start, 3),
                'end': round(end, 3),
                'duration_sec': round(duration, 3),
                'is_rest': True,
                'freq_hz': None,
                'midi': None,
                'vi_name': 'Nghỉ',
                'en_name': 'Rest',
                'label': 'R',
                'label_en': 'Rest',
                'octave': None,
                **duration_to_note_type(duration, tempo),
                'duration_vi': duration_to_note_type(duration, tempo)['vi_name'],
            })
            continue

        note_info = freq_to_note(pitch)
        dur_info = duration_to_note_type(duration, tempo)

        notes.append({
            'index': i + 1,
            'start': round(start, 3),
            'end': round(end, 3),
            'duration_sec': round(duration, 3),
            'is_rest': False,
            **note_info,
            **dur_info,
            'duration_vi': dur_info['vi_name'],
        })

    return {
        'notes': notes,
        'tempo_bpm': round(tempo, 2),
        'total_duration': round(total_duration, 3),
        'sr': sr,
        'num_notes': sum(1 for n in notes if not n.get('is_rest')),
        'num_rests': sum(1 for n in notes if n.get('is_rest')),
    }
