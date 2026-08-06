"""
===================================================================
RETROLENS PRO: CYBERPUNK STYLUS FOCUS & RETRO CAMERA STUDIO
===================================================================
Aplikasi Lensa Kamera Interaktif dengan Mode Stylus Focus & Anti-Trigger Palsu.

Pembaruan Anti-Trigger Palsu (100% Permanen):
1. Pengujian Geometris Jarak 5 Jari (is_valid_open_palm):
   - Mencegah pemicuan tidak sengaja akibat miringnya tangan saat membentuk bingkai.
2. Tahan Telapak 5 Jari Secara Sengaja Selama 1.5 Detik:
   - Harus menahan telapak tangan 5 jari terbuka secara sengaja selama 1.5 detik penuh.
   - Dilengkapi Indikator Kemajuan Visual Countdown % di Layar.
   - Jika tangan bergerak/berubah sebelum 1.5s, timer otomatis reset.
===================================================================
"""

import cv2
import numpy as np
import time
import math
import random
import argparse
from datetime import datetime
from hand_tracking_module import HandDetector


def is_valid_open_palm(lm_list):
    """
    Validasi Geometris Telapak Tangan Terbuka Penuh.
    Memastikan seluruh 5 ujung jari (4, 8, 12, 16, 20) terentang jauh dari pergelangan tangan (0).
    """
    if len(lm_list) < 21:
        return False
    wrist = lm_list[0]
    tips = [4, 8, 12, 16, 20]
    mcps = [2, 5, 9, 13, 17]
    for tip, mcp in zip(tips, mcps):
        dist_tip = math.hypot(lm_list[tip][1] - wrist[1], lm_list[tip][2] - wrist[2])
        dist_mcp = math.hypot(lm_list[mcp][1] - wrist[1], lm_list[mcp][2] - wrist[2])
        if dist_tip <= dist_mcp * 1.15:
            return False
    return True


class RetroLensEngine:
    """
    Mesin Memori & Penghalus Gerakan Bingkai RetroLens.
    Melacak posisi Tangan Kiri & Kanan secara independen dengan memori anti-hilang.
    """
    def __init__(self, alpha=0.35, max_persist_frames=15):
        self.alpha = alpha
        self.max_persist = max_persist_frames
        self.left_hand_pts = None   # [P1 (Index), P4 (Thumb)]
        self.right_hand_pts = None  # [P2 (Index), P3 (Thumb)]
        self.left_missed = 0
        self.right_missed = 0

    def update(self, detected_hands_list):
        if len(detected_hands_list) >= 2:
            h0 = detected_hands_list[0]
            h1 = detected_hands_list[1]
            if h0[8][1] < h1[8][1]:
                raw_left, raw_right = h0, h1
            else:
                raw_left, raw_right = h1, h0

            left_target = [(raw_left[8][1], raw_left[8][2]), (raw_left[4][1], raw_left[4][2])]
            right_target = [(raw_right[8][1], raw_right[8][2]), (raw_right[4][1], raw_right[4][2])]

            self._update_left(left_target)
            self._update_right(right_target)

        elif len(detected_hands_list) == 1:
            raw_h = detected_hands_list[0]
            target_pts = [(raw_h[8][1], raw_h[8][2]), (raw_h[4][1], raw_h[4][2])]
            
            dist_left = 99999
            dist_right = 99999
            if self.left_hand_pts is not None:
                dist_left = math.hypot(target_pts[0][0] - self.left_hand_pts[0][0], target_pts[0][1] - self.left_hand_pts[0][1])
            if self.right_hand_pts is not None:
                dist_right = math.hypot(target_pts[0][0] - self.right_hand_pts[0][0], target_pts[0][1] - self.right_hand_pts[0][1])

            if dist_left <= dist_right:
                self._update_left(target_pts)
                self.right_missed += 1
            else:
                self._update_right(target_pts)
                self.left_missed += 1

        else:
            self.left_missed += 1
            self.right_missed += 1

        valid_left = (self.left_hand_pts is not None) and (self.left_missed <= self.max_persist)
        valid_right = (self.right_hand_pts is not None) and (self.right_missed <= self.max_persist)

        if valid_left and valid_right:
            p1 = (int(self.left_hand_pts[0][0]), int(self.left_hand_pts[0][1]))    # Top-Left
            p4 = (int(self.left_hand_pts[1][0]), int(self.left_hand_pts[1][1]))    # Bottom-Left
            p2 = (int(self.right_hand_pts[0][0]), int(self.right_hand_pts[0][1]))  # Top-Right
            p3 = (int(self.right_hand_pts[1][0]), int(self.right_hand_pts[1][1]))  # Bottom-Right
            return [p1, p2, p3, p4], True
        
        return None, False

    def _update_left(self, target):
        self.left_missed = 0
        if self.left_hand_pts is None:
            self.left_hand_pts = [np.array(target[0], dtype=np.float32), np.array(target[1], dtype=np.float32)]
        else:
            self.left_hand_pts[0] += self.alpha * (np.array(target[0], dtype=np.float32) - self.left_hand_pts[0])
            self.left_hand_pts[1] += self.alpha * (np.array(target[1], dtype=np.float32) - self.left_hand_pts[1])

    def _update_right(self, target):
        self.right_missed = 0
        if self.right_hand_pts is None:
            self.right_hand_pts = [np.array(target[0], dtype=np.float32), np.array(target[1], dtype=np.float32)]
        else:
            self.right_hand_pts[0] += self.alpha * (np.array(target[0], dtype=np.float32) - self.right_hand_pts[0])
            self.right_hand_pts[1] += self.alpha * (np.array(target[1], dtype=np.float32) - self.right_hand_pts[1])


def apply_lens_filter(img_roi, filter_mode):
    """Menerapkan Filter Lensa Kamera pada Region of Interest (ROI)."""
    h, w, _ = img_roi.shape
    if h <= 0 or w <= 0:
        return img_roi

    if filter_mode == "GLITCH":
        glitch = img_roi.copy()
        shift = max(6, w // 25)
        b, g, r = cv2.split(glitch)
        r_shifted = np.roll(r, shift, axis=1)
        b_shifted = np.roll(b, -shift, axis=1)
        glitch = cv2.merge([b_shifted, g, r_shifted])

        num_slices = 4
        for _ in range(num_slices):
            slice_h = random.randint(4, max(5, h // 12))
            y_start = random.randint(0, max(0, h - slice_h))
            offset = random.choice([-20, -12, 12, 20])
            glitch[y_start:y_start + slice_h, :, :] = np.roll(
                glitch[y_start:y_start + slice_h, :, :], offset, axis=1
            )

        glitch[::3, :, :] = (glitch[::3, :, :] * 0.7).astype(np.uint8)
        return glitch

    elif filter_mode == "MONO":
        gray = cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    elif filter_mode == "NIGHTVISION":
        gray = cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY)
        nv = np.zeros_like(img_roi)
        nv[:, :, 1] = cv2.add(gray, 40)
        nv[:, :, 0] = (gray * 0.15).astype(np.uint8)
        nv[:, :, 2] = (gray * 0.1).astype(np.uint8)
        nv[::2, :, :] = (nv[::2, :, :] * 0.8).astype(np.uint8)
        return nv

    elif filter_mode == "CYBER":
        gray = cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 120)
        edges_bgr = np.zeros_like(img_roi)
        edges_bgr[:, :, 0] = edges
        edges_bgr[:, :, 1] = (edges * 0.9).astype(np.uint8)
        edges_bgr[:, :, 2] = (edges * 0.4).astype(np.uint8)
        return edges_bgr

    elif filter_mode == "THERMAL":
        gray = cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY)
        return cv2.applyColorMap(gray, cv2.COLORMAP_JET)

    elif filter_mode == "SEPIA":
        kernel_sepia = np.array([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ])
        sepia = cv2.transform(img_roi, kernel_sepia)
        return np.clip(sepia, 0, 255).astype(np.uint8)

    return img_roi


def draw_corner_bracket(img, pt, length=22, color=(0, 215, 255), thickness=3, direction=(1, 1)):
    """Menggambar Siku-Siku (L-Bracket) Futuristik di Setiap Sudut Bingkai."""
    x, y = pt
    dx, dy = direction
    cv2.line(img, (x, y), (x + dx * length, y), color, thickness)
    cv2.line(img, (x, y), (x, y + dy * length), color, thickness)


def draw_grid_overlay(img, pts_src, grid_divisions=3):
    """Menggambar Garis Grid Rule of Thirds di Dalam Bingkai Fleksibel."""
    p1, p2, p3, p4 = pts_src
    for i in range(1, grid_divisions):
        t = i / grid_divisions
        top_pt = (int(p1[0] * (1 - t) + p2[0] * t), int(p1[1] * (1 - t) + p2[1] * t))
        bot_pt = (int(p4[0] * (1 - t) + p3[0] * t), int(p4[1] * (1 - t) + p3[1] * t))
        cv2.line(img, top_pt, bot_pt, (0, 255, 255), 1, cv2.LINE_AA)
        
        left_pt = (int(p1[0] * (1 - t) + p4[0] * t), int(p1[1] * (1 - t) + p4[1] * t))
        right_pt = (int(p2[0] * (1 - t) + p3[0] * t), int(p2[1] * (1 - t) + p3[1] * t))
        cv2.line(img, left_pt, right_pt, (0, 255, 255), 1, cv2.LINE_AA)


def calculate_aspect_ratio_str(w, h):
    """Menghitung Rasio Aspek Bingkai."""
    if h <= 0 or w <= 0:
        return "FREE"
    ratio = w / h
    if abs(ratio - (16 / 9)) < 0.15:
        return "16:9"
    elif abs(ratio - (4 / 3)) < 0.15:
        return "4:3"
    elif abs(ratio - 1.0) < 0.15:
        return "1:1 SQUARE"
    else:
        return f"{ratio:.2f}:1"


def render_neon_glow_canvas(img, glow_canvas):
    """
    Menggabungkan Kanvas Lukisan Neon Glow ke Frame Utama dengan Efek Gaussian Blur Aura.
    """
    if np.count_nonzero(glow_canvas) == 0:
        return img
    
    glow_blur = cv2.GaussianBlur(glow_canvas, (21, 21), 0)
    img = cv2.addWeighted(img, 1.0, glow_blur, 0.85, 0)
    img = cv2.addWeighted(img, 1.0, glow_canvas, 1.0, 0)
    return img


def run_retro_lens(cam_idx=0):
    cap = cv2.VideoCapture(cam_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"[ERROR] Kamera Index {cam_idx} tidak dapat dibuka!")
        return

    detector = HandDetector(max_hands=2, detection_con=0.4, track_con=0.4)
    engine = RetroLensEngine(alpha=0.35, max_persist_frames=15)

    filters = ["GLITCH", "MONO", "NIGHTVISION", "CYBER", "THERMAL", "SEPIA", "NORMAL"]
    filter_idx = 0
    photo_count = 0
    prev_time = 0
    
    flash_frames = 0
    pinch_start_time = 0
    show_grid = True

    # State Glow Stylus Focus Mode & Intentional Palm Hold Timer
    stylus_focus_mode = False
    palm_hold_start_time = 0

    glow_canvas = None
    xp, yp = 0, 0
    neon_colors = [
        {"name": "CYAN GLOW", "color": (255, 255, 0)},
        {"name": "PINK NEON", "color": (255, 0, 255)},
        {"name": "LIME GREEN", "color": (0, 255, 0)},
        {"name": "GOLD LIGHT", "color": (0, 215, 255)},
        {"name": "WHITE LASER", "color": (255, 255, 255)}
    ]
    color_idx = 0

    print("=========================================================")
    print("  RETROLENS PRO: CYBERPUNK STYLUS FOCUS & RETRO CAMERA   ")
    print("=========================================================")
    print(" GESTUR TERKONTROL DENGAN TIMER SENGAN (ANTI-FALSE TRIGGER):")
    print(" - Tahan 1 Tangan (5 Jari Terbuka) SENGASA SELAMA 1.5 DETIK -> TOGGLE STYLUS FOCUS!")
    print(" - Tekan 'e' pada keyboard jika ingin beralih secara instan.")
    print(" Navigasi Keyboard:")
    print("   [e]         : Toggle Mode Stylus Focus (Masuk/Keluar)")
    print("   [v]         : Ganti Warna Neon Stylus")
    print("   [c]         : Bersihkan Kanvas Lukisan Glow")
    print("   [f] / [TAB] : Ganti Filter Kamera")
    print("   [g]         : Toggle Grid Lines")
    print("   [SPACE] /[s]: Capture Foto Instant Shutter")
    print("   [q] / [ESC] : Keluar")
    print("=========================================================\n")

    while True:
        success, img = cap.read()
        if not success:
            time.sleep(0.01)
            continue

        img = cv2.flip(img, 1)
        h, w, _ = img.shape
        filter_mode = filters[filter_idx]

        if glow_canvas is None or glow_canvas.shape != img.shape:
            glow_canvas = np.zeros((h, w, 3), dtype=np.uint8)

        # Scanlines CRT Retro di Latar Belakang
        img[::4, :, :] = (img[::4, :, :] * 0.92).astype(np.uint8)

        # Deteksi Tangan
        img = detector.find_hands(img, draw=False, draw_box=False)

        detected_hands = []
        for h_idx in range(len(detector.current_landmarks)):
            lm_list = detector.find_positions(img, hand_no=h_idx, draw=False)
            if len(lm_list) > 8:
                detected_hands.append(lm_list)

        # --- DETEKSI GESTUR 5 JARI SENGASA SELAMA 1.5 DETIK (INTENTIONAL HOLD TIMER) ---
        open_palm_detected = False
        if len(detected_hands) == 1: # Harus 1 tangan tunggal terbuka penuh!
            lm_h = detected_hands[0]
            if is_valid_open_palm(lm_h):
                open_palm_detected = True

        if open_palm_detected:
            if palm_hold_start_time == 0:
                palm_hold_start_time = time.time()
            elapsed_palm = time.time() - palm_hold_start_time
            progress_palm = min(1.0, elapsed_palm / 1.5)

            # Tampilkan Indikator Kemajuan Timer Countdown di Layar
            target_str = "TOGGLE RETRO FRAMING" if stylus_focus_mode else "STYLUS FOCUS MODE"
            cv2.rectangle(img, (w // 2 - 200, 110), (w // 2 + 200, 145), (30, 30, 50), cv2.FILLED)
            cv2.rectangle(img, (w // 2 - 200, 110), (w // 2 + 200, 145), (0, 255, 255), 2)
            cv2.putText(img, f"TAHAN 5 JARI: {target_str} ({int(progress_palm * 100)}%)",
                        (w // 2 - 185, 133), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 255), 1)

            if elapsed_palm >= 1.5:
                stylus_focus_mode = not stylus_focus_mode
                palm_hold_start_time = 0
                print(f"[STYLUS GESTURE SENGASA] Mode Stylus Focus: {'AKTIF' if stylus_focus_mode else 'NONAKTIF'}")
        else:
            palm_hold_start_time = 0

        pts_smooth, has_frame = engine.update(detected_hands)
        pinch_detected = False
        roll_deg = 0

        # --- MODE 1: BINGKAI RETROLENS (HANYA AKTIF JIKA TIDAK DALAM MODE STYLUS FOCUS!) ---
        if has_frame and not stylus_focus_mode:
            p1, p2, p3, p4 = pts_smooth
            pts_src = np.array([p1, p2, p3, p4], dtype=np.float32)

            if len(detected_hands) > 0:
                for h_lms in detected_hands:
                    p_dist = math.hypot(h_lms[4][1] - h_lms[8][1], h_lms[4][2] - h_lms[8][2])
                    if p_dist < 25:
                        pinch_detected = True

            w_top = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            w_bottom = math.hypot(p3[0] - p4[0], p3[1] - p4[1])
            max_w = int(max(w_top, w_bottom))

            h_right = math.hypot(p3[0] - p2[0], p3[1] - p2[1])
            h_left = math.hypot(p4[0] - p1[0], p4[1] - p1[1])
            max_h = int(max(h_right, h_left))

            if max_w > 30 and max_h > 30:
                pts_dst = np.array([
                    [0, 0],
                    [max_w - 1, 0],
                    [max_w - 1, max_h - 1],
                    [0, max_h - 1]
                ], dtype=np.float32)

                M = cv2.getPerspectiveTransform(pts_src, pts_dst)
                M_inv = cv2.getPerspectiveTransform(pts_dst, pts_src)

                warped = cv2.warpPerspective(img, M, (max_w, max_h))
                filtered_warped = apply_lens_filter(warped, filter_mode)
                filtered_back = cv2.warpPerspective(filtered_warped, M_inv, (w, h))

                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.fillConvexPoly(mask, pts_src.astype(np.int32), 255)
                mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

                img = np.where(mask_3ch == 255, filtered_back, img)

                if show_grid:
                    draw_grid_overlay(img, pts_src)

                # Overlay Bingkai HUD
                cv2.polylines(img, [pts_src.astype(np.int32)], True, (0, 255, 200), 2, cv2.LINE_AA)

                for pt in [p1, p2, p3, p4]:
                    cv2.circle(img, (pt[0], pt[1]), 7, (0, 255, 255), cv2.FILLED)
                    cv2.circle(img, (pt[0], pt[1]), 10, (255, 255, 255), 2)

                draw_corner_bracket(img, (p1[0], p1[1]), direction=(1, 1))
                draw_corner_bracket(img, (p2[0], p2[1]), direction=(-1, 1))
                draw_corner_bracket(img, (p3[0], p3[1]), direction=(-1, -1))
                draw_corner_bracket(img, (p4[0], p4[1]), direction=(1, -1))

                cx = int((p1[0] + p2[0] + p3[0] + p4[0]) / 4)
                cy = int((p1[1] + p2[1] + p3[1] + p4[1]) / 4)
                cv2.line(img, (cx - 12, cy), (cx + 12, cy), (255, 255, 255), 2)
                cv2.line(img, (cx, cy - 12), (cx, cy + 12), (255, 255, 255), 2)

                aspect_str = calculate_aspect_ratio_str(max_w, max_h)
                label_pos = (int((p1[0] + p2[0]) / 2) - 80, int((p1[1] + p2[1]) / 2) - 12)
                cv2.putText(img, f"{filter_mode} | {aspect_str} | {max_w}x{max_h}", label_pos,
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                angle_rad = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
                roll_deg = int(math.degrees(angle_rad))

        # --- MODE 2: EFEK DITHERING / REDUP KAMERA (HANYA AKTIF SAAT MODE STYLUS FOCUS!) ---
        if stylus_focus_mode:
            dark_bg = np.zeros_like(img)
            img = cv2.addWeighted(img, 0.45, dark_bg, 0.55, 0)

            cv2.rectangle(img, (w // 2 - 210, 68), (w // 2 + 210, 102), (20, 20, 40), cv2.FILLED)
            cv2.rectangle(img, (w // 2 - 210, 68), (w // 2 + 210, 102), (0, 255, 255), 2)
            cv2.putText(img, f"★ STYLUS FOCUS: {neon_colors[color_idx]['name']} ★", (w // 2 - 195, 91),
                        cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 255, 255), 2)

            if len(detected_hands) > 0:
                for h_idx, h_lms in enumerate(detected_hands):
                    hand_type = detector.get_hand_type(h_idx)
                    fingers = detector.fingers_up(h_lms, hand_type)

                    x1, y1 = h_lms[8][1], h_lms[8][2]
                    x2, y2 = h_lms[12][1], h_lms[12][2]

                    # 1 Jari Telunjuk -> Melukis Neon!
                    if fingers[1] == 1 and fingers[2] == 0:
                        current_glow_color = neon_colors[color_idx]["color"]

                        cv2.circle(img, (x1, y1), 8, current_glow_color, cv2.FILLED)
                        cv2.circle(img, (x1, y1), 12, (255, 255, 255), 2)

                        if xp == 0 and yp == 0:
                            xp, yp = x1, y1

                        cv2.line(glow_canvas, (xp, yp), (x1, y1), current_glow_color, 6, cv2.LINE_AA)
                        xp, yp = x1, y1

                    # 2 Jari -> Hover Kursor
                    elif fingers[1] == 1 and fingers[2] == 1:
                        xp, yp = 0, 0
                        cv2.circle(img, (x1, y1), 10, neon_colors[color_idx]["color"], 2)
                        cv2.circle(img, (x2, y2), 10, neon_colors[color_idx]["color"], 2)
                    else:
                        xp, yp = 0, 0
            else:
                xp, yp = 0, 0
        else:
            xp, yp = 0, 0

        # RENDER LUKISAN NEON GLOW PADA SCREEN
        img = render_neon_glow_canvas(img, glow_canvas)

        # --- AUTO PINCH GESTURE SNAPSHOT COUNTDOWN ---
        if pinch_detected and not stylus_focus_mode:
            if pinch_start_time == 0:
                pinch_start_time = time.time()
            elapsed = time.time() - pinch_start_time
            progress = min(1.0, elapsed / 1.0)
            cv2.putText(img, f"HOLD PINCH FOR SNAP: {int(progress * 100)}%", (w // 2 - 160, 115),
                        cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 255, 0), 2)
            
            if elapsed >= 1.0:
                photo_count += 1
                filename = f"retrolens_{filter_mode}_{int(time.time())}.png"
                cv2.imwrite(filename, img)
                print(f"[GESTURE AUTO SNAP] Foto berhasil ditangkap: '{filename}'")
                flash_frames = 4
                pinch_start_time = 0
        else:
            pinch_start_time = 0

        # --- VISUAL CAMERA SHUTTER FLASH EFFECT ---
        if flash_frames > 0:
            flash_overlay = np.ones_like(img) * 255
            cv2.addWeighted(flash_overlay, 0.7, img, 0.3, 0, img)
            cv2.putText(img, "📸 SHUTTER SNAP!", (w // 2 - 140, h // 2),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 3)
            flash_frames -= 1

        # --- RETRO HUD OVERLAYS ---
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        if int(time.time() * 2) % 2 == 0:
            cv2.circle(img, (45, 35), 8, (0, 0, 255), cv2.FILLED)
        cv2.putText(img, "REC", (62, 42), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, now_str, (w - 280, 42), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        # Bottom Status Bar HUD
        overlay_bottom = img.copy()
        cv2.rectangle(overlay_bottom, (0, h - 50), (w, h), (15, 15, 25), cv2.FILLED)
        cv2.addWeighted(overlay_bottom, 0.7, img, 0.3, 0, img)
        cv2.line(img, (0, h - 50), (w, h - 50), (0, 255, 200), 1)

        stylus_status = "STYLUS FOCUS (ACTIVE)" if stylus_focus_mode else "RETRO FRAMING (Tahan 5 Jari 1.5s -> Stylus)"
        bottom_str = f"RETROLENS | {filter_mode} | {stylus_status} | FPS {int(fps)} | FOTO {photo_count}"
        angle_str = f"ROLL {roll_deg:+}deg | PITCH -4deg | YAW +2deg"

        cv2.putText(img, bottom_str, (20, h - 18), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(img, angle_str, (w - 380, h - 18), cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 215, 255), 2)

        cv2.imshow("RETROLENS PRO - Flexible Hand Framing Camera", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            print("[INFO] Menghentikan RetroLens Pro...")
            break
        elif key == ord('e') or key == ord('E'):
            stylus_focus_mode = not stylus_focus_mode
            print(f"[STYLUS] Toggle Stylus Focus Mode: {'AKTIF (Retro Framing Nonaktif)' if stylus_focus_mode else 'NONAKTIF (Retro Framing Aktif)'}")
        elif key == ord('v') or key == ord('V'):
            color_idx = (color_idx + 1) % len(neon_colors)
            print(f"[STYLUS] Berpindah ke Warna Neon: {neon_colors[color_idx]['name']}")
        elif key == ord('c') or key == ord('C'):
            glow_canvas = np.zeros((h, w, 3), dtype=np.uint8)
            print("[STYLUS] Kanvas lukisan glow berhasil dibersihkan!")
        elif key == ord('f') or key == 9:
            filter_idx = (filter_idx + 1) % len(filters)
            print(f"[FILTER] Berpindah ke filter: {filters[filter_idx]}")
        elif key == ord('g') or key == ord('G'):
            show_grid = not show_grid
            print(f"[GRID] Grid Overlay: {'Aktif' if show_grid else 'Nonaktif'}")
        elif key == 32 or key == ord('s'):
            photo_count += 1
            filename = f"retrolens_{filter_mode}_{int(time.time())}.png"
            cv2.imwrite(filename, img)
            print(f"[CAPTURE] Snapshot manual disimpan sebagai '{filename}'")
            flash_frames = 4

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RetroLens Pro Camera Framing Tool")
    parser.add_argument("--cam", type=int, default=0, help="Indeks Kamera (Default: 0)")
    args = parser.parse_args()
    run_retro_lens(cam_idx=args.cam)
