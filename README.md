# Drone — Phát Hiện Nốt Nhạc Từ File MP3

Nhét file MP3 (hoặc WAV/FLAC) vào, hệ thống tự động phát hiện:
- **Cao độ**: Đô, Rê, Mi, Fa, Sol, La, Si (+ quãng tám, dấu thăng/giáng)
- **Trường độ**: Nốt tròn, Nốt trắng, Nốt đen, Móc đơn, Móc kép, Móc ba
- **Tempo** (BPM) ước tính tự động
- **Piano roll** trực quan (PNG)

## Cài đặt

```bash
pip install -r requirements.txt
# Cần ffmpeg để đọc file MP3:
# Ubuntu:  sudo apt install ffmpeg
# macOS:   brew install ffmpeg
```

## Cách dùng

```bash
# Phát hiện nốt nhạc
python detect_notes.py bai_nhac.mp3

# Lưu kết quả JSON + hình piano roll
python detect_notes.py bai_nhac.mp3 --output ket_qua.json --visual piano_roll.png

# Tùy chỉnh độ nhạy
python detect_notes.py bai_nhac.mp3 --delta 0.05 --wait 60
```

### Ví dụ kết quả

```
  Tempo     : 90.0 BPM
  Thời lượng: 12.45s
  Tổng nốt  : 15  |  Nghỉ: 0

    #   Bắt đầu   Cao độ (VI)    Cao độ (EN)     Trường độ      Ký hiệu  Thời gian
  ────────────────────────────────────────────────────────────────────────────────
    1.     0.00s       Đô           C4           Nốt đen        ♩        0.667s
    2.     0.70s       Rê           D4           Nốt đen        ♩        0.667s
    3.     1.39s       Mi           E4           Nốt đen        ♩        0.667s
    ...
    8.     4.88s       Đô           C5          Nốt trắng       𝅗𝅥       1.333s
    9.     6.24s       Si           B4           Móc đơn        ♪        0.333s
```

## Tham số CLI

| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `--delta` | 0.07 | Ngưỡng onset (thấp = nhạy hơn, phát hiện nhiều nốt hơn) |
| `--wait` | 80 | Khoảng cách tối thiểu giữa các nốt (ms) |
| `--output` | - | Lưu JSON kết quả |
| `--visual` | - | Lưu hình piano roll PNG |
| `--no-trim` | - | Không cắt khoảng lặng đầu/cuối |
| `--json-only` | - | Chỉ in JSON ra stdout |

## Kiến trúc

```
detect_notes.py          <- CLI chinh
src/
├── audio_loader.py      <- Load MP3/WAV/FLAC -> numpy array
├── onset_detector.py    <- Phat hien diem bat dau not + tempo
├── pitch_detector.py    <- Phat hien cao do (thuat toan pYIN)
├── note_classifier.py   <- Phan loai truong do (den/trang/moc...)
├── note_mapper.py       <- Tan so Hz -> ten not VI/EN
└── visualizer.py        <- Ve piano roll
examples/
├── generate_test_audio.py   <- Tao file WAV test
├── c_major_scale.wav        <- Gam Do truong (test)
└── happy_birthday.wav       <- Happy Birthday (test)
```

## Thuat toan

1. **Load audio** — librosa, SR = 22050 Hz, mono
2. **Uoc tinh tempo** — librosa beat tracker + fallback autocorrelation
3. **Onset detection** — librosa onset envelope, backtracking
4. **Pitch detection** — pYIN (probabilistic YIN), median co trong so
5. **Phan loai** — so sanh thoi luong thuc / beat de xac dinh loai not
6. **Mapping** — Hz -> MIDI -> ten not Do/Re/Mi...

> **Luu y**: Thuat toan pYIN cho ket qua tot nhat voi **nhac don am** (mot not tai mot thoi diem). Nhac da am (nhieu nhac cu cung luc) se kem chinh xac hon.
