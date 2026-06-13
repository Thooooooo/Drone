"""Visualize detected notes as a piano roll and waveform plot."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba


_CMAP = plt.cm.Set2


def _pitch_class_color(midi_num: int) -> tuple:
    return _CMAP(midi_num % 12 / 12)


def plot_piano_roll(
    notes: list[dict],
    total_duration: float,
    tempo_bpm: float,
    output_path: str,
    title: str = "Nốt nhạc phát hiện được",
) -> None:
    """Save a piano roll visualization to output_path."""
    if not notes:
        return

    midi_values = [n['midi'] for n in notes if n.get('midi') is not None]
    if not midi_values:
        return

    midi_min = max(int(min(midi_values)) - 3, 21)
    midi_max = min(int(max(midi_values)) + 3, 108)

    fig_w = max(12, total_duration * 1.5)
    fig_h = max(4, (midi_max - midi_min) * 0.3 + 2)

    fig, axes = plt.subplots(2, 1, figsize=(fig_w, fig_h),
                              gridspec_kw={'height_ratios': [3, 1]})

    ax_roll = axes[0]
    ax_roll.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0f0f23')

    # Draw piano key grid lines
    for midi in range(midi_min, midi_max + 1):
        pc = midi % 12
        is_black = pc in (1, 3, 6, 8, 10)
        lw = 0.3 if not is_black else 0.1
        color = '#2a2a4a' if not is_black else '#1a1a3a'
        ax_roll.axhline(midi, color=color, linewidth=lw, zorder=0)

    # Beat grid
    beat_dur = 60.0 / max(tempo_bpm, 20.0)
    beat = 0.0
    while beat <= total_duration:
        ax_roll.axvline(beat, color='#3a3a5a', linewidth=0.5, zorder=0)
        beat += beat_dur

    # Draw notes
    for n in notes:
        if n.get('midi') is None:
            continue
        midi = n['midi']
        start = n['start']
        dur = n['duration_sec']
        color = _pitch_class_color(int(round(midi)))
        rect = mpatches.FancyBboxPatch(
            (start, midi - 0.4), dur * 0.92, 0.8,
            boxstyle='round,pad=0.02',
            linewidth=0.5,
            edgecolor='white',
            facecolor=color,
            alpha=0.9,
            zorder=2,
        )
        ax_roll.add_patch(rect)
        # Label short notes with vi_name
        if dur > beat_dur * 0.4:
            ax_roll.text(
                start + dur * 0.05, midi,
                n.get('vi_name', ''),
                color='white', fontsize=6, va='center',
                fontweight='bold', zorder=3,
            )

    ax_roll.set_xlim(0, total_duration)
    ax_roll.set_ylim(midi_min - 0.5, midi_max + 0.5)
    ax_roll.set_ylabel('MIDI / Cao độ', color='white', fontsize=9)
    ax_roll.tick_params(colors='white')
    ax_roll.spines[:].set_color('#3a3a5a')

    # Y-tick labels with Vietnamese names
    from src.note_mapper import midi_to_note_parts
    yticks = range(midi_min, midi_max + 1, 2)
    ylabels = []
    for m in yticks:
        vi, en, en_s, oct_ = midi_to_note_parts(m)
        ylabels.append(f'{en_s}{oct_}')
    ax_roll.set_yticks(list(yticks))
    ax_roll.set_yticklabels(ylabels, fontsize=7, color='#cccccc')

    ax_roll.set_title(
        f'{title}  |  Tempo: {tempo_bpm:.1f} BPM  |  {len(notes)} nốt',
        color='white', fontsize=11, pad=8,
    )

    # Bottom axis: note duration type timeline
    ax_dur = axes[1]
    ax_dur.set_facecolor('#1a1a2e')
    for n in notes:
        if n.get('midi') is None:
            continue
        color = _pitch_class_color(int(round(n['midi'])))
        ax_dur.barh(
            0, n['duration_sec'], left=n['start'],
            height=0.6, color=color, alpha=0.8, edgecolor='white', linewidth=0.3,
        )
        ax_dur.text(
            n['start'] + n['duration_sec'] * 0.05, 0,
            n.get('duration_vi', ''),
            color='white', fontsize=5.5, va='center', zorder=3,
        )

    ax_dur.set_xlim(0, total_duration)
    ax_dur.set_ylim(-0.5, 0.5)
    ax_dur.set_yticks([])
    ax_dur.set_xlabel('Thời gian (giây)', color='white', fontsize=9)
    ax_dur.tick_params(colors='white')
    ax_dur.spines[:].set_color('#3a3a5a')
    ax_dur.set_ylabel('Trường độ', color='white', fontsize=7)

    plt.tight_layout(pad=0.5)
    fig.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [Hình] Đã lưu: {output_path}")
