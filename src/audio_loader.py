"""Load audio files (MP3, WAV, FLAC, OGG) into numpy arrays."""

import os
import warnings
import numpy as np

_SR_DEFAULT = 22050


def load_audio(path: str, sr: int = _SR_DEFAULT, mono: bool = True) -> tuple[np.ndarray, int]:
    """Load an audio file and return (audio_array, sample_rate).

    Supports MP3 (requires ffmpeg), WAV, FLAC, OGG.
    Returns float32 array normalised to [-1, 1].
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    # Try librosa first (handles WAV, FLAC, OGG natively; MP3 via ffmpeg/audioread)
    try:
        import librosa
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            y, sr_loaded = librosa.load(path, sr=sr, mono=mono)
        return y, sr_loaded
    except Exception as librosa_err:
        pass

    # Fallback: pydub → WAV in memory (works with MP3 if ffmpeg available)
    if ext in ('.mp3', '.m4a', '.aac', '.ogg'):
        try:
            from pydub import AudioSegment
            import io
            seg = AudioSegment.from_file(path)
            seg = seg.set_frame_rate(sr).set_channels(1 if mono else seg.channels)
            samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
            samples /= 2 ** (8 * seg.sample_width - 1)
            return samples, sr
        except Exception as pydub_err:
            raise RuntimeError(
                f"Cannot load '{path}'.\n"
                "For MP3 files, please install ffmpeg:\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  macOS:         brew install ffmpeg\n"
                "  Windows:       https://ffmpeg.org/download.html\n"
                f"Original error: {librosa_err}"
            ) from pydub_err

    raise RuntimeError(f"Unsupported audio format: {ext}")


def normalize_audio(y: np.ndarray) -> np.ndarray:
    """Peak-normalize audio to [-1, 1]."""
    peak = np.max(np.abs(y))
    if peak > 0:
        return y / peak
    return y


def trim_silence(y: np.ndarray, sr: int, top_db: float = 30.0) -> np.ndarray:
    """Trim leading/trailing silence."""
    import librosa
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
    return y_trimmed


def audio_info(path: str) -> dict:
    """Return basic info about an audio file without fully loading it."""
    import soundfile as sf
    try:
        info = sf.info(path)
        return {
            'path': path,
            'samplerate': info.samplerate,
            'channels': info.channels,
            'duration_sec': info.duration,
            'format': info.format,
        }
    except Exception:
        return {'path': path}
