"""Detect the pitch (fundamental frequency) of each note segment."""

import numpy as np
import librosa

_FMIN = librosa.note_to_hz('C2')   # ~65 Hz
_FMAX = librosa.note_to_hz('C7')   # ~2093 Hz


def detect_pitch_segment(
    y: np.ndarray,
    sr: int,
    fmin: float = _FMIN,
    fmax: float = _FMAX,
) -> float | None:
    """Return the dominant pitch (Hz) of an audio segment using pYIN.

    Returns None if no clear pitch is detected (silence / noise).
    """
    min_len = int(sr * 0.05)  # pYIN needs at least ~50ms
    if len(y) < min_len:
        y = np.pad(y, (0, min_len - len(y)))

    try:
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=fmin,
            fmax=fmax,
            sr=sr,
            hop_length=512,
        )
    except Exception:
        return None

    voiced_f0 = f0[voiced_flag & ~np.isnan(f0)]
    if len(voiced_f0) == 0:
        return None

    # Weighted median: weight by voiced probability
    voiced_probs_filtered = voiced_probs[voiced_flag & ~np.isnan(f0)]
    weights = np.clip(voiced_probs_filtered, 0, 1)
    if weights.sum() == 0:
        return float(np.median(voiced_f0))

    sorted_idx = np.argsort(voiced_f0)
    sorted_f0 = voiced_f0[sorted_idx]
    sorted_w = weights[sorted_idx]
    cum_w = np.cumsum(sorted_w)
    median_idx = np.searchsorted(cum_w, cum_w[-1] * 0.5)
    return float(sorted_f0[min(median_idx, len(sorted_f0) - 1)])


def detect_pitch_all_segments(
    y: np.ndarray,
    sr: int,
    segments: list[tuple[float, float]],
) -> list[float | None]:
    """Detect pitch for every (start_sec, end_sec) segment."""
    pitches = []
    for start, end in segments:
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        segment_audio = y[start_sample:end_sample]
        if len(segment_audio) == 0:
            pitches.append(None)
            continue
        pitches.append(detect_pitch_segment(segment_audio, sr))
    return pitches


def is_silence(y_segment: np.ndarray, threshold_db: float = -40.0) -> bool:
    """Return True if the segment is silence (RMS below threshold)."""
    if len(y_segment) == 0:
        return True
    rms = np.sqrt(np.mean(y_segment ** 2))
    if rms < 1e-10:
        return True
    rms_db = 20 * np.log10(rms)
    return rms_db < threshold_db
