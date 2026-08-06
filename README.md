# 🖐️ Python Hand Tracking & RetroLens Pro Studio

Tools **Hand Tracking & Gesture Recognition** interaktif berbasis Python menggunakan framework **MediaPipe** dan **OpenCV**. Dilengkapi dengan 4 mode pengaplikasian dunia nyata: Tracking HUD, Air Canvas, Virtual Controller, dan **RetroLens Pro Camera Studio**.

---

## 🌟 Fitur Unggulan

### 📸 RetroLens Pro: Flexible Hand Framing Camera Studio
1. **Bingkai Tangan Fleksibel (Perspective Warp)**:
   - Membingkai kamera secara real-time menggunakan 4 sudut jari dari 2 tangan (Telunjuk Kiri, Telunjuk Kanan, Jempol Kanan, Jempol Kiri).
   - Bingkai mengikuti rotasi, sudut tilt, dan jarak pergerakan tangan di udara.

2. **6 Filter Lensa Kamera Futuristik**:
   - 🖤 **`MONO`**: Hitam putih kontras tinggi dengan CLAHE adaptive contrast (sesuai contoh gambar acuan!).
   - 👾 **`GLITCH`**: Efek Cyberpunk RGB Channel Shift / Chromatic Aberration & CRT Scanlines.
   - 🟢 **`NIGHTVISION`**: Penglihatan malam Green Phosphor ala Goggles militer.
   - ⚡ **`CYBER`**: Neon Glowing Canny Edge Outline (Blue/Cyan/Magenta).
   - 🔥 **`THERMAL`**: Infra-Red Heatmap Color Map (Jet palette).
   - 📜 **`SEPIA`**: Tone warna film vintage klasik tahun 1970-an.

3. **Auto-Pinch Gesture Photo Capture (Jepret Otomatis Jari)**:
   - Merapatkan ujung jempol & telunjuk (<25px) selama 1 detik akan **memicu Jepretan Foto Otomatis** dilengkapi **Efek Visual Shutter Flash `📸 SHUTTER SNAP!`**.

4. **Dynamic Aspect Ratio & Grid Hologram**:
   - Menghitung rasio bingkai secara real-time (`16:9`, `4:3`, `1:1 Square`).
   - Garis Grid Hologram *Rule of Thirds* yang dapat diaktifkan/dinonaktifkan (Tekan `g`).
   - Overlay Retro HUD: Indikator kedap-kedip `● REC`, Crosshair `+`, Siku Sudut Kuning, dan derajat `Roll / Pitch / Yaw`.

---

## 📁 Struktur Direktori

```text
hand_tracker/
├── hand_tracking_module.py  # Modul Class HandDetector (Dual MediaPipe API support)
├── main.py                  # Aplikasi utama 4 Mode All-in-One
├── retro_lens.py            # Standalone RetroLens Pro Studio
├── demo_simple.py           # Script minimalis (~30 baris)
├── hand_landmarker.task     # Model MediaPipe Tasks API
├── requirements.txt         # Dependency package
└── README.md                # Dokumentasi lengkap
```

---

## 🚀 Cara Menjalankan

```bash
# Jalankan Aplikasi Utama (Mode 1-4):
python main.py

# Atau Jalankan RetroLens Pro Studio Langsung:
python retro_lens.py
```

#### 🎮 Kontrol Keyboard di RetroLens Pro:
| Tombol | Aksi |
| :--- | :--- |
| **`f`** / **`TAB`** | Ganti 6 Filter Lensa (`MONO` ➔ `GLITCH` ➔ `NIGHTVISION` ➔ `CYBER` ➔ `THERMAL` ➔ `SEPIA`) |
| **`g`** | Toggle Garis Grid Hologram (*Rule of Thirds*) |
| **`SPACE`** / **`s`** | Shutter Capture Photo Manual |
| **`Gestur Pinch`** | Merapatkan Jempol & Telunjuk 1 Detik -> Auto Snapshot Shutter Flash |
| **`q`** / **`ESC`** | Keluar |
