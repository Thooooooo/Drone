"""Generate a synthetic test WAV file with a known melody (C major scale + simple tune)."""

import numpy as np
import soundfile as sf
import os

SR = 22050

# C major scale frequencies (middle octave)
NOTES = {
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25,
    'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
}


def sine_note(freq: float, duration: float, sr: int = SR, fade: float = 0.02) -> np.ndarray:
    """Generate a sine wave with fade-in/out envelope."""
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    wave = 0.6 * np.sin(2 * np.pi * freq * t)
    # Add harmonics for more realism
    wave += 0.2 * np.sin(2 * np.pi * freq * 2 * t)
    wave += 0.1 * np.sin(2 * np.pi * freq * 3 * t)
    # Fade envelope
    fade_len = int(fade * sr)
    if fade_len > 0 and len(wave) > fade_len * 2:
        wave[:fade_len] *= np.linspace(0, 1, fade_len)
        wave[-fade_len:] *= np.linspace(1, 0, fade_len)
    return wave


def silence(duration: float, sr: int = SR) -> np.ndarray:
    return np.zeros(int(duration * sr))


def generate_scale_wav(output_path: str, tempo_bpm: float = 120.0):
    """Generate a C major scale (whole → half → quarter → eighth notes)."""
    beat = 60.0 / tempo_bpm  # quarter note duration

    melody = [
        # (note_name, beats)
        ('C4', 1.0), ('D4', 1.0), ('E4', 1.0), ('F4', 1.0),
        ('G4', 1.0), ('A4', 1.0), ('B4', 1.0), ('C5', 2.0),
        # Going down with variety
        ('B4', 0.5), ('A4', 0.5), ('G4', 1.0), ('F4', 0.5), ('E4', 0.5),
        ('D4', 2.0), ('C4', 4.0),
    ]

    audio_parts = []
    for note_name, beats in melody:
        freq = NOTES[note_name]
        dur = beats * beat
        audio_parts.append(sine_note(freq, dur))
        audio_parts.append(silence(0.03))  # tiny gap between notes

    audio = np.concatenate(audio_parts)
    audio = audio / np.max(np.abs(audio)) * 0.8  # normalise

    sf.write(output_path, audio, SR)
    print(f"Generated: {output_path}  ({len(audio)/SR:.2f}s, {tempo_bpm} BPM)")

    # Print expected notes
    print("\nExpected notes:")
    beat = 60.0 / tempo_bpm
    t = 0.0
    for note_name, beats in melody:
        dur = beats * beat
        print(f"  {t:.2f}s  {note_name:<4}  {beats} beat(s)  = {dur:.3f}s")
        t += dur + 0.03


def generate_happy_birthday(output_path: str, tempo_bpm: float = 100.0):
    """Generate Happy Birthday tune (simple melody test)."""
    beat = 60.0 / tempo_bpm

    # Happy Birthday in C major (simplified)
    melody = [
        ('C4', 0.75), ('C4', 0.25), ('D4', 1.0),
        ('C4', 1.0),  ('F4', 1.0),  ('E4', 2.0),
        ('C4', 0.75), ('C4', 0.25), ('D4', 1.0),
        ('C4', 1.0),  ('G4', 1.0),  ('F4', 2.0),
        ('C4', 0.75), ('C4', 0.25), ('C5', 1.0),
        ('A4', 1.0),  ('F4', 1.0),  ('E4', 1.0), ('D4', 1.0),
        ('B4', 0.75), ('B4', 0.25), ('A4', 1.0),
        ('F4', 1.0),  ('G4', 1.0),  ('F4', 2.0),
    ]

    audio_parts = []
    for note_name, beats in melody:
        freq = NOTES[note_name]
        dur = beats * beat
        audio_parts.append(sine_note(freq, dur))
        audio_parts.append(silence(0.025))

    audio = np.concatenate(audio_parts)
    audio = audio / np.max(np.abs(audio)) * 0.8
    sf.write(output_path, audio, SR)
    print(f"Generated: {output_path}  ({len(audio)/SR:.2f}s, {tempo_bpm} BPM)")


if __name__ == '__main__':
    os.makedirs('examples', exist_ok=True)
    generate_scale_wav('examples/c_major_scale.wav', tempo_bpm=90)
    print()
    generate_happy_birthday('examples/happy_birthday.wav', tempo_bpm=100)
