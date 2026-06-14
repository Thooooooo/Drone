"""Render detected notes as traditional Western sheet music on a staff."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from matplotlib.patches import Ellipse

# ─── Geometry ──────────────────────────────────────────────────────────────────
LINE_SP  = 1.0            # distance between adjacent staff lines (data units)
_HS      = LINE_SP / 2    # half-step: y-distance between adjacent staff positions
HEAD_RX  = 0.38           # note head x-radius (data units)
HEAD_RY  = 0.28           # note head y-radius
STEM_LEN = 3.5 * LINE_SP  # standard stem length
BEAT_W   = 3.2            # x-units per quarter-note beat
CLEF_W   = 3.8            # x reserved for clef + time sig
BEATS_SYS = 8             # beats per system line (2 bars of 4/4)

# Pitch class → diatonic step within octave (C=0 … B=6)
_PC_DIA = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
_E4_DIA = 4 * 7 + 2  # diatonic number of E4 = 30


# ─── Coordinate helpers ────────────────────────────────────────────────────────

def _pos_y(pos: int) -> float:
    """Staff position → y coordinate.  0 = E4 (bottom line), 8 = F5 (top)."""
    return pos * _HS


def _midi_to_staff(midi: float) -> tuple[int, bool]:
    """Return (staff_pos, has_accidental).  staff_pos: integer grid position."""
    m = int(round(midi))
    pc  = m % 12
    oct_ = m // 12 - 1
    dia  = oct_ * 7 + _PC_DIA[pc]
    pos  = dia - _E4_DIA
    acc  = pc in (1, 3, 6, 8, 10)
    return pos, acc


# ─── Drawing primitives ────────────────────────────────────────────────────────

def _staff(ax, x0: float, x1: float) -> None:
    for i in range(5):
        y = i * LINE_SP
        ax.plot([x0, x1], [y, y], color='black', lw=0.85, zorder=1)


def _treble_clef(ax, x: float) -> None:
    """Draw treble clef glyph on G4 line using FreeSerif (has music Unicode block)."""
    from matplotlib.font_manager import findfont, FontProperties
    fp = FontProperties(family='FreeSerif')
    font_path = findfont(fp)
    y = _pos_y(2)  # G4 line
    ax.text(x + 0.05, y - LINE_SP * 0.35, '\U0001D11E',
            fontsize=34, va='bottom', ha='left', color='black', zorder=8,
            clip_on=False, fontproperties=fp)


def _time_sig(ax, x: float, num: int = 4, den: int = 4) -> None:
    kw = dict(ha='center', fontweight='bold', color='black', zorder=8, clip_on=False)
    ax.text(x, _pos_y(6), str(num), fontsize=14, va='center', **kw)
    ax.text(x, _pos_y(2), str(den), fontsize=14, va='center', **kw)


def _bar_line(ax, x: float, y0: float, y1: float) -> None:
    ax.plot([x, x], [y0, y1], color='black', lw=0.85, zorder=3)


def _ledger_lines(ax, x: float, pos: int) -> None:
    lx0, lx1 = x - HEAD_RX - 0.45, x + HEAD_RX + 0.45
    # below staff (even positions ≤ -2)
    if pos <= -2:
        for p in range(0, pos - 1, -2):
            if p <= -2:
                y = _pos_y(p)
                ax.plot([lx0, lx1], [y, y], 'k-', lw=0.85, zorder=4)
    # above staff (even positions ≥ 10)
    if pos >= 10:
        for p in range(10, pos + 2, 2):
            y = _pos_y(p)
            ax.plot([lx0, lx1], [y, y], 'k-', lw=0.85, zorder=4)


def _flag(ax, sx: float, y_flag_top: float, stem_up: bool) -> None:
    """Draw one flag as a bezier curve from the tip of the stem."""
    fx  = sx + HEAD_RX * 2.4
    dir_ = -1 if stem_up else 1
    fy  = y_flag_top + dir_ * LINE_SP * 0.95
    cy  = y_flag_top + dir_ * LINE_SP * 0.30
    cx  = sx + HEAD_RX * 1.1
    verts = [(sx, y_flag_top), (cx, cy), (fx, fy)]
    codes = [mpath.Path.MOVETO, mpath.Path.CURVE3, mpath.Path.CURVE3]
    patch = mpatches.PathPatch(
        mpath.Path(verts, codes),
        fc='none', ec='black', lw=1.0, zorder=5
    )
    ax.add_patch(patch)


def _whole_note_head(ax, x: float, y: float) -> None:
    outer = Ellipse((x, y), HEAD_RX * 2.5, HEAD_RY * 2.0,
                    angle=0, fc='white', ec='black', lw=0.9, zorder=6)
    inner = Ellipse((x + HEAD_RX * 0.12, y), HEAD_RX * 1.0, HEAD_RY * 1.1,
                    angle=-25, fc='white', ec='white', lw=0, zorder=7)
    ax.add_patch(outer)
    ax.add_patch(inner)


def _dot(ax, x: float, y: float, pos: int) -> None:
    """Augmentation dot to the right of note head (offset if on a line)."""
    dy = _HS * 0.5 if pos % 2 == 0 else 0  # move up if note sits on a line
    ax.add_patch(Ellipse((x + HEAD_RX + 0.42, y + dy),
                          0.22, 0.22, fc='black', ec='none', zorder=7))


def _draw_note(ax, x: float, n: dict) -> None:
    """Draw a single note with head, stem, flags, ledger lines, and labels."""
    midi = n.get('midi')
    if midi is None:
        return

    pos, has_acc = _midi_to_staff(midi)
    y   = _pos_y(pos)
    bv  = n.get('beat_value', 1.0)

    is_whole = bv >= 4.0
    is_half  = 2.0 <= bv < 4.0
    filled   = bv < 2.0                          # quarter and shorter
    flags    = (3 if bv <= 0.125 else
                2 if bv <= 0.25  else
                1 if bv <= 0.5   else 0)
    dotted   = bv in (3.0, 1.5, 0.75, 0.375, 0.1875)
    stem_up  = pos <= 4   # stem up when note ≤ B4 (middle of staff)

    _ledger_lines(ax, x, pos)

    # accidental
    if has_acc:
        ax.text(x - HEAD_RX - 0.42, y, '♯',
                fontsize=10, ha='center', va='center', color='black', zorder=6)

    # note head
    if is_whole:
        _whole_note_head(ax, x, y)
    else:
        fc = 'black' if filled else 'white'
        ax.add_patch(Ellipse((x, y), HEAD_RX * 2, HEAD_RY * 2,
                              angle=-20, fc=fc, ec='black', lw=0.9, zorder=6))

    # augmentation dot
    if dotted:
        _dot(ax, x, y, pos)

    # stem + flags
    if not is_whole:
        if stem_up:
            sx   = x + HEAD_RX * 0.88
            sy0  = y + HEAD_RY * 0.3
            sy1  = sy0 + STEM_LEN
        else:
            sx   = x - HEAD_RX * 0.88
            sy0  = y - HEAD_RY * 0.3
            sy1  = sy0 - STEM_LEN
        ax.plot([sx, sx], [sy0, sy1], 'k-', lw=0.85, zorder=5)

        flag_dir = -1 if stem_up else 1
        for fi in range(flags):
            fy = sy1 + fi * flag_dir * LINE_SP * 0.58
            _flag(ax, sx, fy, stem_up)

    # ── Labels ────────────────────────────────────────────────────────────────
    # Decide label position: below staff or above if note is very low
    label_y = min(y, _pos_y(0)) - 2.4
    vi_name = n.get('vi_name', '')
    dur_vi  = n.get('duration_vi', '')
    freq    = n.get('freq_hz')

    ax.text(x, label_y,        vi_name,
            fontsize=8, ha='center', va='top',
            color='#1565c0', fontweight='bold', zorder=9)
    ax.text(x, label_y - 0.75, dur_vi,
            fontsize=6.5, ha='center', va='top', color='#6a1b9a', zorder=9)
    if freq:
        ax.text(x, label_y - 1.4, f'{freq:.0f}Hz',
                fontsize=5.5, ha='center', va='top', color='#888888', zorder=9)


def _draw_rest(ax, x: float, bv: float, dur_vi: str) -> None:
    """Draw a rest symbol."""
    y_rest = _pos_y(5)  # rests sit around D5 space
    sym = ('𝄻' if bv >= 4 else '𝄼' if bv >= 2 else
           '𝄽' if bv >= 1 else '𝄾' if bv >= 0.5 else '𝄿')
    ax.text(x, y_rest, sym, fontsize=16, ha='center', va='center',
            color='black', zorder=7)
    ax.text(x, _pos_y(0) - 2.4, 'Nghỉ',
            fontsize=8, ha='center', va='top', color='#888', fontweight='bold')
    ax.text(x, _pos_y(0) - 3.15, dur_vi,
            fontsize=6.5, ha='center', va='top', color='#aaa')


# ─── Main entry point ──────────────────────────────────────────────────────────

def render_sheet_music(
    notes: list,
    tempo_bpm: float,
    output_path: str,
    title: str = "Bản nhạc phát hiện được",
    beats_per_system: int = BEATS_SYS,
    show_rests: bool = False,
) -> None:
    """Render notes as sheet music and save PNG to output_path."""
    work = [n for n in notes
            if (n.get('midi') is not None or (show_rests and n.get('is_rest')))
            and not (n.get('is_rest') and not show_rests)]

    if not work:
        print("  [Sheet] Không có nốt hợp lệ để vẽ.")
        return

    # ── Group into systems ────────────────────────────────────────────────────
    systems: list[list] = []
    cur: list = []
    cur_b = 0.0
    for n in work:
        bv = n.get('beat_value', 1.0)
        if cur_b + bv > beats_per_system + 0.001 and cur:
            systems.append(cur)
            cur = [n]; cur_b = bv
        else:
            cur.append(n); cur_b += bv
    if cur:
        systems.append(cur)

    # ── Dynamic y-range ───────────────────────────────────────────────────────
    all_pos = []
    for n in work:
        if n.get('midi') is not None:
            p, _ = _midi_to_staff(n['midi'])
            all_pos.append(p)
    pos_min = min(all_pos) if all_pos else 0
    pos_max = max(all_pos) if all_pos else 8
    stem_top_y  = _pos_y(max(pos_max, 8)) + STEM_LEN + 1.2
    label_bot_y = _pos_y(min(pos_min, 0)) - 4.5

    # ── Figure ────────────────────────────────────────────────────────────────
    n_sys  = len(systems)
    fig_w  = 15.0
    h_sys  = (stem_top_y - label_bot_y) * 0.38 + 0.8  # inches per system
    h_sys  = max(h_sys, 3.8)
    fig_h  = n_sys * h_sys + 1.6
    fig    = plt.figure(figsize=(fig_w, fig_h), facecolor='white')

    fig.text(0.5, 1 - 0.32 / fig_h, title,
             ha='center', va='top', fontsize=14, fontweight='bold', color='#1a237e')
    fig.text(0.5, 1 - 0.82 / fig_h, f'Tempo: {tempo_bpm:.0f} BPM',
             ha='center', va='top', fontsize=9, color='#555')

    # ── Render each system ────────────────────────────────────────────────────
    for si, sys_notes in enumerate(systems):
        total_b = sum(n.get('beat_value', 1.0) for n in sys_notes)
        x_max   = CLEF_W + total_b * BEAT_W + 1.8

        # Axes position (top-down)
        top  = (fig_h - 1.45 - si * h_sys) / fig_h
        bot  = top - (h_sys * 0.90) / fig_h
        ax   = fig.add_axes([0.015, max(bot, 0.01), 0.97, max((top - max(bot, 0.01)), 0.05)])
        ax.set_xlim(0, x_max)
        ax.set_ylim(label_bot_y, stem_top_y)
        ax.set_facecolor('white')
        ax.axis('off')

        y_staff_bot = _pos_y(0)
        y_staff_top = _pos_y(8)

        # staff + clef
        _staff(ax, 0.3, x_max - 0.3)
        _treble_clef(ax, 0.4)

        # time sig on first system
        x_cur = CLEF_W - 0.2
        if si == 0:
            _time_sig(ax, x_cur)
            x_cur += 1.3

        # opening bar line
        _bar_line(ax, x_cur - 0.5, y_staff_bot, y_staff_top)

        # notes
        measure_beat = 0.0
        beats_per_measure = 4.0
        for n in sys_notes:
            bv = n.get('beat_value', 1.0)
            # bar line when measure is complete
            if measure_beat >= beats_per_measure - 0.001 and measure_beat > 0:
                _bar_line(ax, x_cur - 0.35, y_staff_bot, y_staff_top)
                measure_beat -= beats_per_measure

            if n.get('is_rest'):
                _draw_rest(ax, x_cur, bv, n.get('duration_vi', ''))
            else:
                _draw_note(ax, x_cur, n)

            x_cur        += bv * BEAT_W
            measure_beat += bv

        # closing double bar line
        _bar_line(ax, x_cur - 0.3, y_staff_bot, y_staff_top)
        _bar_line(ax, x_cur - 0.05, y_staff_bot, y_staff_top)

        # system index label
        ax.text(0.12, _pos_y(4), f'[{si + 1}]',
                fontsize=7, ha='left', va='center', color='#aaa')

    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  [Sheet] Đã lưu: {output_path}")
