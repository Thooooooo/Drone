#!/usr/bin/env python3
"""
detect_notes.py — Phát hiện nốt nhạc từ file MP3/WAV/FLAC

Cách dùng:
    python detect_notes.py bai_nhac.mp3
    python detect_notes.py bai_nhac.mp3 --output ket_qua.json
    python detect_notes.py bai_nhac.mp3 --visual piano_roll.png
    python detect_notes.py bai_nhac.mp3 --delta 0.05 --wait 60
"""

import argparse
import json
import sys
import os

# Ensure src/ is importable when running from project root
sys.path.insert(0, os.path.dirname(__file__))


DURATION_SYMBOLS = {
    'Nốt tròn đôi':  '𝅜  ',
    'Nốt tròn':      '𝅝  ',
    'Trắng chấm':    '𝅗𝅥. ',
    'Nốt trắng':     '𝅗𝅥  ',
    'Đen chấm':      '♩. ',
    'Nốt đen':       '♩  ',
    'Móc đơn chấm':  '♪. ',
    'Móc đơn':       '♪  ',
    'Móc kép chấm':  '𝅘𝅥𝅯. ',
    'Móc kép':       '𝅘𝅥𝅯  ',
    'Móc ba':        '𝅘𝅥𝅰  ',
}


def print_banner():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           🎵  PHÁT HIỆN NỐT NHẠC TỪ FILE ÂM THANH          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()


def print_results(result: dict) -> None:
    notes = result['notes']
    tempo = result['tempo_bpm']
    total_dur = result['total_duration']

    print(f"  Tempo    : {tempo} BPM")
    print(f"  Thời lượng: {total_dur:.2f}s")
    print(f"  Tổng nốt : {result['num_notes']}  |  Nghỉ: {result['num_rests']}")
    print()

    # Table header
    hdr = f"  {'#':>3}  {'Bắt đầu':>8}  {'Cao độ (VI)':^14}  {'Cao độ (EN)':^8}  {'Trường độ':^16}  {'Ký hiệu':^6}  {'Thời gian':>8}"
    print(hdr)
    print("  " + "─" * (len(hdr) - 2))

    for n in notes:
        idx     = n['index']
        start   = f"{n['start']:.2f}s"
        vi      = n.get('vi_name', '-')
        en      = n.get('label_en', n.get('en_name', '-'))
        dur_vi  = n.get('duration_vi', '-')
        symbol  = DURATION_SYMBOLS.get(dur_vi, '   ')
        dur_s   = f"{n['duration_sec']:.3f}s"

        rest_mark = " 🎵" if not n.get('is_rest') else " 🎼"
        print(f"  {idx:>3}.  {start:>8}  {vi:^14}  {en:^8}  {dur_vi:^16}  {symbol:^6}  {dur_s:>8}{rest_mark}")

    print()
    print("  Ghi chú loại nốt:")
    print("  ♩ Nốt đen (1 phách)  ♪ Móc đơn (½ phách)  𝅘𝅥𝅯 Móc kép (¼ phách)")
    print("  𝅗𝅥 Nốt trắng (2 phách)  𝅝 Nốt tròn (4 phách)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Phát hiện nốt nhạc từ file MP3/WAV/FLAC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('audio', help="Đường dẫn file âm thanh (mp3, wav, flac...)")
    parser.add_argument('--output', '-o', help="Lưu kết quả JSON ra file")
    parser.add_argument('--visual', '-v', help="Lưu hình piano roll ra file PNG")
    parser.add_argument(
        '--delta', type=float, default=0.07,
        help="Ngưỡng nhận diện onset (0.01–0.3, thấp=nhiều hơn, mặc định: 0.07)",
    )
    parser.add_argument(
        '--wait', type=float, default=80,
        help="Khoảng cách tối thiểu giữa các nốt (ms, mặc định: 80)",
    )
    parser.add_argument(
        '--no-trim', action='store_true',
        help="Không cắt khoảng lặng đầu/cuối",
    )
    parser.add_argument(
        '--json-only', action='store_true',
        help="Chỉ in JSON ra stdout, không in bảng",
    )
    args = parser.parse_args()

    if not args.json_only:
        print_banner()
        print(f"  File: {args.audio}")
        print()

    from src.detector import detect_notes

    try:
        result = detect_notes(
            args.audio,
            onset_delta=args.delta,
            wait_ms=args.wait,
            trim=not args.no_trim,
        )
    except FileNotFoundError as e:
        print(f"\n  Lỗi: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n  Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print()
    print("═" * 70)
    print("  KẾT QUẢ PHÁT HIỆN NỐT NHẠC")
    print("═" * 70)
    print_results(result)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  [JSON] Đã lưu: {args.output}")

    if args.visual:
        from src.visualizer import plot_piano_roll
        plot_piano_roll(
            notes=[n for n in result['notes'] if not n.get('is_rest')],
            total_duration=result['total_duration'],
            tempo_bpm=result['tempo_bpm'],
            output_path=args.visual,
        )

    print("  Hoàn tất!")
    print()


if __name__ == '__main__':
    main()
