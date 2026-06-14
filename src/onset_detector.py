"""Detect note onsets and segment audio into individual note regions."""

import numpy as np
import librosa


def detect_onsets(
    y: np.ndarray,
    sr: int,
    delta: float = 0.07,
    wait_ms: float = 80,
) -> np.ndarray:
    """Detect note onsets and return their times in seconds.

    delta: sensitivity threshold (higher = fewer, more confident onsets)
    wait_ms: minimum gap between onsets in milliseconds
    """
    wait_frames = int(wait_ms / 1000 * sr / 512)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=512,
        delta=delta,
        wait=wait_frames,
        backtrack=True,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
    return onset_times


def estimate_tempo(y: np.ndarray, sr: int) -> tuple[float, np.ndarray]:
    """Estimate tempo (BPM) and beat times."""
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=512)
    # tempo may be an array in newer librosa versions
    if hasattr(tempo, '__len__'):
        tempo = float(tempo[0])
    else:
        tempo = float(tempo)
    # Fallback: estimate from inter-onset intervals
    if tempo < 20:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
        try:
            ac = librosa.autocorrelate(onset_env, max_size=int(sr * 2 / 512))
            # Search for tempo in 40–240 BPM range
            hop = 512
            bpm_lo, bpm_hi = 40.0, 240.0
            frames_hi = int(60.0 / bpm_lo * sr / hop)
            frames_lo = max(1, int(60.0 / bpm_hi * sr / hop))
            ac_clip = ac[frames_lo:frames_hi]
            if ac_clip.size > 0:
                best_frame = frames_lo + int(np.argmax(ac_clip))
                tempo = 60.0 / (best_frame * hop / sr)
        except Exception:
            pass
    # Hard floor so division is always safe
    if tempo < 20 or not np.isfinite(tempo):
        tempo = 120.0
    return tempo, beat_times


def build_note_segments(
    onset_times: np.ndarray,
    total_duration: float,
    min_duration: float = 0.05,
) -> list[tuple[float, float]]:
    """Convert onset times to (start, end) segments.

    The end of each note is the start of the next onset.
    The last note ends at total_duration.
    """
    segments = []
    times = list(onset_times) + [total_duration]
    for i in range(len(times) - 1):
        start = times[i]
        end = times[i + 1]
        if end - start >= min_duration:
            segments.append((float(start), float(end)))
    return segments
