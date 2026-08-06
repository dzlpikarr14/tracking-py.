"""
===================================================================
VIRTUAL HAND TRACKER & INTERACTIVE GESTURE TOOL (MediaPipe + OpenCV)
===================================================================
Aplikasi serbaguna dengan 4 Mode Utama:
1. Mode 1 [Tracking HUD]: Deteksi Landmark, Jenis Tangan, Jari, & FPS HUD.
2. Mode 2 [Air Canvas]: Melukis di Udara menggunakan Jari Telunjuk.
3. Mode 3 [Virtual Pinch Controller]: Pengontrol Slider / Volume Virtual.
4. Mode 4 [RetroLens Pro Framing Studio]: Kamera Bingkai Tangan Fleksibel
   dengan Mode Stylus Focus (Diaktifkan Tahan 5 Jari Sengaja 1.5s / 'e').

Navigasi Shortcut Keyboard:
- Tekan '1' : Pindah ke Mode Tracking HUD
- Tekan '2' : Pindah ke Mode Air Canvas (Melukis Udara)
- Tekan '3' : Pindah ke Mode Virtual Pinch Controller
- Tekan '4' : Pindah ke Mode RetroLens Pro Framing
- Tekan 'e' / Tahan 5 Jari 1.5s : Masuk/Keluar Mode Stylus Focus (Layar Meredup)
- Tekan 'v' : Ganti Warna Neon Glow Stylus (Cyan, Pink, Green, Gold, White)
- Tekan 'f' : Ganti 6 Filter Kamera (GLITCH, MONO, NIGHTVISION, CYBER, THERMAL, SEPIA)
- Tekan 'g' : Toggle Grid Hologram / Rule of Thirds Lines (Mode 4)
- Tekan 'c' : Bersihkan Kanvas Lukis Glow
- Tekan 's' / SPACE : Simpan Tangkapan Layar (Screenshot / Shutter Flash)
- Tekan 'q' atau ESC : Keluar dari Aplikasi
===================================================================
"""

import cv2
import numpy as np
import time
import math
import argparse
from datetime import datetime
from hand_tracking_module import HandDetector
from retro_lens import (
    apply_lens_filter,
    draw_corner_bracket,
    draw_grid_overlay,
    calculate_aspect_ratio_str,
    render_neon_glow_canvas,
    is_valid_open_palm,
    RetroLensEngine
)


def draw_hud_panel(img, title, mode_str, fps, cam_idx=0):
    """Menggambar Top Dashboard HUD yang Futuristik."""
    h, w, _ = img.shape
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (15, 15, 25), cv2.FILLED)
    alpha = 0.7
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    cv2.line(img, (0, 60), (w, 60), (0, 255, 200), 2)
    cv2.putText(img, title, (20, 38), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(img, f"SRC: Cam {cam_idx} | Mode: {mode_str}", (w // 2 - 160, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)
    
    fps_color = (0, 255, 0) if fps >= 20 else (0, 165, 255)
    cv2.putText(img, f"FPS: {int(fps)}", (w - 140, 38), cv2.FONT_HERSHEY_DUPLEX, 0.8, fps_color, 2)


def run_app(cam_idx=0):
    cap = cv2.VideoCapture(cam_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"[ERROR] Kamera Index {cam_idx} tidak dapat diakses!")
        return

    detector = HandDetector(mode=False, max_hands=2, detection_con=0.4, track_con=0.4)
    engine = RetroLensEngine(alpha=0.35, max_persist_frames=15)
    
    current_mode = 1
    prev_time = 0
    
    # Variables Mode 2
    brush_thickness = 10
    eraser_thickness = 50
    draw_color = (255, 0, 128)
    xp, yp = 0, 0
    img_canvas = None
    colors_palette = [
        {"name": "Merah", "color": (0, 0, 255)},
        {"name": "Hijau", "color": (0, 255, 0)},
        {"name": "Biru", "color": (255, 150, 0)},
        {"name": "Kuning", "color": (0, 255, 255)},
        {"name": "Penghapus", "color": (0, 0, 0)}
    ]
    
    # Variables Mode 3
    vol_bar = 400
    vol_per = 0

    # Variables Mode 4 (RetroLens Pro & Stylus Focus)
    filters = ["GLITCH", "MONO", "NIGHTVISION", "CYBER", "THERMAL", "SEPIA", "NORMAL"]
    filter_idx = 0
    photo_count = 0
    flash_frames = 0
    pinch_start_time = 0
    show_grid = True

    stylus_focus_mode = False
    palm_hold_start_time = 0

    glow_canvas = None
    xp_glow, yp_glow = 0, 0
    neon_colors = [
        {"name": "CYAN GLOW", "color": (255, 255, 0)},
        {"name": "PINK NEON", "color": (255, 0, 255)},
        {"name": "LIME GREEN", "color": (0, 255, 0)},
        {"name": "GOLD LIGHT", "color": (0, 215, 255)},
        {"name": "WHITE LASER", "color": (255, 255, 255)}
    ]
    color_idx = 0

    print("=====================================================")
    print("      HAND TRACKER TOOL PYTHON (MediaPipe + OpenCV)  ")
    print("=====================================================")
    print(" Navigasi Keyboard:")
    print("   [1] : Mode Tracking & HUD Jari")
    print("   [2] : Mode Air Canvas (Melukis Udara)")
    print("   [3] : Mode Virtual Controller Slider")
    print("   [4] : Mode RetroLens Pro Flexible Framing Kamera")
    print("   [e] / Tahan 5 Jari 1.5s : Masuk/Keluar Mode Stylus Focus")
    print("   [v] : Ganti Warna Neon Glow Stylus (Di Mode 4)")
    print("   [f] : Ganti 6 Filter Kamera (GLITCH, MONO, NIGHTVISION...)")
    print("   [g] : Toggle Grid Hologram (Di Mode 4)")
    print("   [c] : Hapus Kanvas Lukis")
    print("   [s] / SPACE : Simpan Screenshot (Camera Shutter Flash)")
    print("   [q] : Keluar")
    print("=====================================================\n")

    while True:
        success, img = cap.read()
        if not success:
            time.sleep(0.01)
            continue

        img = cv2.flip(img, 1)
        h, w, c = img.shape

        if img_canvas is None or img_canvas.shape != img.shape:
            img_canvas = np.zeros((h, w, 3), np.uint8)
        if glow_canvas is None or glow_canvas.shape != img.shape:
            glow_canvas = np.zeros((h, w, 3), np.uint8)

        img = detector.find_hands(img, draw=(current_mode != 4), draw_box=(current_mode == 1))
        lm_list = detector.find_positions(img, hand_no=0, draw=False)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        # -------------------------------------------------------------
        # MODE 1: TRACKING HUD
        # -------------------------------------------------------------
        if current_mode == 1:
            draw_hud_panel(img, "HAND TRACKING HUD", "1. Tracking & Gestur", fps, cam_idx)

            if len(lm_list) != 0:
                hand_type = detector.get_hand_type(0)
                fingers = detector.fingers_up(lm_list, hand_type)
                total_fingers = sum(fingers)

                overlay_box = img.copy()
                cv2.rectangle(overlay_box, (20, h - 180), (340, h - 20), (20, 20, 35), cv2.FILLED)
                cv2.addWeighted(overlay_box, 0.7, img, 0.3, 0, img)
                cv2.rectangle(img, (20, h - 180), (340, h - 20), (0, 255, 200), 2)

                cv2.putText(img, f"Jenis: {hand_type}", (35, h - 145),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                cv2.putText(img, f"Total Jari: {total_fingers} / 5", (35, h - 115),
                            cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 0), 2)

                names = ["Jempol", "Telunjuk", "Tengah", "Manis", "Kelingking"]
                status_str = " ".join([f"{n[0]}:{v}" for n, v in zip(names, fingers)])
                cv2.putText(img, f"Status: {status_str}", (35, h - 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

                length, img, _ = detector.find_distance(4, 8, img, lm_list, draw=True)
                cv2.putText(img, f"Jarak Pinch: {int(length)} px", (35, h - 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
            else:
                cv2.putText(img, "Tunjukkan Tangan Anda di Depan Kamera...",
                            (w // 2 - 250, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

        # -------------------------------------------------------------
        # MODE 2: AIR CANVAS
        # -------------------------------------------------------------
        elif current_mode == 2:
            draw_hud_panel(img, "AIR CANVAS - MELUKIS UDARA", "2. Lukis Udara", fps, cam_idx)

            box_w = w // len(colors_palette)
            for i, col in enumerate(colors_palette):
                x1, y1 = i * box_w, 62
                x2, y2 = (i + 1) * box_w, 110
                cv2.rectangle(img, (x1, y1), (x2, y2), col["color"], cv2.FILLED)
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
                text_col = (0, 0, 0) if col["name"] in ["Kuning", "Hijau", "Penghapus"] else (255, 255, 255)
                cv2.putText(img, col["name"], (x1 + 15, y1 + 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_col, 2)

            if len(lm_list) != 0:
                hand_type = detector.get_hand_type(0)
                fingers = detector.fingers_up(lm_list, hand_type)

                x1, y1 = lm_list[8][1], lm_list[8][2]
                x2, y2 = lm_list[12][1], lm_list[12][2]

                if fingers[1] == 1 and fingers[2] == 1:
                    xp, yp = 0, 0
                    cv2.circle(img, (x1, y1), 12, draw_color, cv2.FILLED)
                    cv2.circle(img, (x2, y2), 12, draw_color, cv2.FILLED)

                    if 62 < y1 < 110:
                        selected_idx = x1 // box_w
                        if 0 <= selected_idx < len(colors_palette):
                            draw_color = colors_palette[selected_idx]["color"]

                elif fingers[1] == 1 and fingers[2] == 0:
                    cv2.circle(img, (x1, y1), 10, draw_color, cv2.FILLED)

                    if xp == 0 and yp == 0:
                        xp, yp = x1, y1

                    if draw_color == (0, 0, 0):
                        cv2.line(img, (xp, yp), (x1, y1), draw_color, eraser_thickness)
                        cv2.line(img_canvas, (xp, yp), (x1, y1), draw_color, eraser_thickness)
                    else:
                        cv2.line(img, (xp, yp), (x1, y1), draw_color, brush_thickness)
                        cv2.line(img_canvas, (xp, yp), (x1, y1), draw_color, brush_thickness)

                    xp, yp = x1, y1
                else:
                    xp, yp = 0, 0
            else:
                xp, yp = 0, 0

            img_gray = cv2.cvtColor(img_canvas, cv2.COLOR_BGR2GRAY)
            _, img_inv = cv2.threshold(img_gray, 20, 255, cv2.THRESH_BINARY_INV)
            img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
            img = cv2.bitwise_and(img, img_inv)
            img = cv2.bitwise_or(img, img_canvas)

            cv2.putText(img, "Petunjuk: [1 Jari Telunjuk] Melukis  |  [2 Jari Telunjuk+Tengah] Pilih Warna  |  [Tekan 'c'] Hapus Kanvas",
                        (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # -------------------------------------------------------------
        # MODE 3: VIRTUAL SLIDER
        # -------------------------------------------------------------
        elif current_mode == 3:
            draw_hud_panel(img, "VIRTUAL PINCH CONTROLLER", "3. Slider Pinch", fps, cam_idx)

            if len(lm_list) != 0:
                length, img, [x1, y1, x2, y2, cx, cy] = detector.find_distance(4, 8, img, lm_list, draw=True)
                vol_bar = np.interp(length, [25, 200], [400, 150])
                vol_per = np.interp(length, [25, 200], [0, 100])

                if length < 30:
                    cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, "LOCKED / CLICK", (cx - 50, cy - 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.rectangle(img, (w - 90, 150), (w - 40, 400), (40, 40, 60), cv2.FILLED)
            cv2.rectangle(img, (w - 90, int(vol_bar)), (w - 40, 400), (0, 255, 200), cv2.FILLED)
            cv2.rectangle(img, (w - 90, 150), (w - 40, 400), (255, 255, 255), 2)
            cv2.putText(img, f'{int(vol_per)} %', (w - 95, 440), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 200), 2)

            cv2.putText(img, "Rapatkan/Renggangkan Jempol & Telunjuk untuk Mengubah Slider",
                        (30, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # -------------------------------------------------------------
        # MODE 4: RETROLENS PRO & STYLUS FOCUS
        # -------------------------------------------------------------
        elif current_mode == 4:
            draw_hud_panel(img, "RETROLENS PRO - FLEXIBLE BINGKAI", f"4. RetroLens ({filters[filter_idx]})", fps, cam_idx)
            filter_mode = filters[filter_idx]

            detected_hands = []
            for h_idx in range(len(detector.current_landmarks)):
                h_lms = detector.find_positions(img, hand_no=h_idx, draw=False)
                if len(h_lms) > 8:
                    detected_hands.append(h_lms)

            # Deteksi Gestur 5 Jari Sengaja dengan Timer 1.5 Detik
            open_palm_detected = False
            if len(detected_hands) == 1:
                lm_h = detected_hands[0]
                if is_valid_open_palm(lm_h):
                    open_palm_detected = True

            if open_palm_detected:
                if palm_hold_start_time == 0:
                    palm_hold_start_time = time.time()
                elapsed_palm = time.time() - palm_hold_start_time
                progress_palm = min(1.0, elapsed_palm / 1.5)

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

            # BINGKAI RETROLENS (HANYA AKTIF JIKA TIDAK DALAM MODE STYLUS FOCUS!)
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

            # EFEK DITHERING / REDUP KAMERA (STYLUS FOCUS OVERLAY)
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

                        if fingers[1] == 1 and fingers[2] == 0:
                            current_glow_color = neon_colors[color_idx]["color"]

                            cv2.circle(img, (x1, y1), 8, current_glow_color, cv2.FILLED)
                            cv2.circle(img, (x1, y1), 12, (255, 255, 255), 2)

                            if xp_glow == 0 and yp_glow == 0:
                                xp_glow, yp_glow = x1, y1

                            cv2.line(glow_canvas, (xp_glow, yp_glow), (x1, y1), current_glow_color, 6, cv2.LINE_AA)
                            xp_glow, yp_glow = x1, y1

                        elif fingers[1] == 1 and fingers[2] == 1:
                            xp_glow, yp_glow = 0, 0
                            cv2.circle(img, (x1, y1), 10, neon_colors[color_idx]["color"], 2)
                            cv2.circle(img, (x2, y2), 10, neon_colors[color_idx]["color"], 2)
                        else:
                            xp_glow, yp_glow = 0, 0
                else:
                    xp_glow, yp_glow = 0, 0
            else:
                xp_glow, yp_glow = 0, 0

            # RENDER LUKISAN NEON GLOW STYLUS
            img = render_neon_glow_canvas(img, glow_canvas)

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

            if flash_frames > 0:
                flash_overlay = np.ones_like(img) * 255
                cv2.addWeighted(flash_overlay, 0.7, img, 0.3, 0, img)
                cv2.putText(img, "📸 SHUTTER SNAP!", (w // 2 - 140, h // 2),
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 3)
                flash_frames -= 1

            cv2.putText(img, "Petunjuk: [Tahan 5 Jari 1.5s / e] Stylus Focus  |  [v] Warna Neon  |  [c] Bersihkan  |  [f] Filter",
                        (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Python Hand Tracker Tool (MediaPipe)", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            print("[INFO] Menghentikan aplikasi...")
            break
        elif key == ord('e') or key == ord('E'):
            stylus_focus_mode = not stylus_focus_mode
            print(f"[STYLUS] Toggle Stylus Focus Mode: {'AKTIF (Retro Framing Nonaktif)' if stylus_focus_mode else 'NONAKTIF (Retro Framing Aktif)'}")
        elif key == ord('v') or key == ord('V'):
            color_idx = (color_idx + 1) % len(neon_colors)
            print(f"[STYLUS] Berpindah ke Warna Neon: {neon_colors[color_idx]['name']}")
        elif key == ord('f') or key == ord('F'):
            filter_idx = (filter_idx + 1) % len(filters)
            print(f"[FILTER] Berpindah ke filter: {filters[filter_idx]}")
        elif key == ord('g') or key == ord('G'):
            show_grid = not show_grid
            print(f"[GRID] Grid Overlay: {'Aktif' if show_grid else 'Nonaktif'}")
        elif key == ord('c') or key == ord('C'):
            glow_canvas = np.zeros((h, w, 3), dtype=np.uint8)
            print("[STYLUS] Kanvas lukisan glow berhasil dibersihkan!")
        elif key == ord('s') or key == ord('S') or key == 32:
            photo_count += 1
            filename = f"retrolens_{filters[filter_idx]}_{int(time.time())}.png"
            cv2.imwrite(filename, img)
            print(f"[SCREENSHOT] Gambar berhasil disimpan sebagai '{filename}'")
            flash_frames = 4

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Hand Tracker Tool")
    parser.add_argument("--cam", type=int, default=0, help="Indeks Kamera (Default: 0)")
    args = parser.parse_args()
    run_app(cam_idx=args.cam)
