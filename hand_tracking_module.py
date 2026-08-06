import cv2
import mediapipe as mp
import math
import time
import os
import urllib.request
import numpy as np


# Hand Connections Constant for Drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),             # Jempol
    (0, 5), (5, 6), (6, 7), (7, 8),             # Telunjuk
    (5, 9), (9, 10), (10, 11), (11, 12),        # Tengah
    (9, 13), (13, 14), (14, 15), (15, 16),      # Manis
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Kelingking & Telapak
]


class HandDetector:
    """
    Modul Pendeteksi Hand Tracking menggunakan MediaPipe & OpenCV.
    Menggunakan MediaPipe Tasks API Video Mode untuk Tracking Real-Time Berkecepatan Tinggi.
    """

    def __init__(self, mode=False, max_hands=2, detection_con=0.4, track_con=0.4, model_path="hand_landmarker.task"):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        self.model_path = model_path
        self.tip_ids = [4, 8, 12, 16, 20]
        
        self.use_tasks_api = not hasattr(mp, 'solutions')

        if self.use_tasks_api:
            self._init_tasks_api()
        else:
            self._init_solutions_api()

        self.current_landmarks = []

    def _init_tasks_api(self):
        if not os.path.exists(self.model_path):
            print(f"[INFO] Mengunduh model '{self.model_path}' dari Google MediaPipe CDN...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            try:
                urllib.request.urlretrieve(url, self.model_path)
                print("[INFO] Unduhan model selesai!")
            except Exception as e:
                print(f"[ERROR] Gagal mengunduh model: {e}")

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        base_options = python.BaseOptions(model_asset_path=self.model_path)
        
        # Gunakan RunningMode.VIDEO untuk tracking kontinyu yang super cepat & smooth!
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO if not self.mode else vision.RunningMode.IMAGE,
            num_hands=self.max_hands,
            min_hand_detection_confidence=float(self.detection_con),
            min_hand_presence_confidence=float(self.track_con),
            min_tracking_confidence=float(self.track_con)
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.start_time = time.time()

    def _init_solutions_api(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=float(self.detection_con),
            min_tracking_confidence=float(self.track_con)
        )

    def find_hands(self, img, draw=True, draw_box=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.current_landmarks = []

        if self.use_tasks_api:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            
            if not self.mode:
                # Video mode tracking dengan timestamp
                timestamp_ms = int((time.time() - self.start_time) * 1000)
                results = self.landmarker.detect_for_video(mp_image, timestamp_ms)
            else:
                results = self.landmarker.detect(mp_image)

            if results.hand_landmarks:
                for idx, hand_lms in enumerate(results.hand_landmarks):
                    handedness_str = "Right"
                    if results.handedness and idx < len(results.handedness):
                        handedness_str = results.handedness[idx][0].category_name

                    self.current_landmarks.append((hand_lms, handedness_str))

                    if draw:
                        self._draw_landmarks_custom(img, hand_lms)
                    if draw_box:
                        self._draw_box_custom(img, hand_lms, handedness_str, idx)
        else:
            results = self.hands.process(img_rgb)
            if results.multi_hand_landmarks:
                for idx, hand_lms in enumerate(results.multi_hand_landmarks):
                    handedness_str = "Right"
                    if results.multi_handedness and idx < len(results.multi_handedness):
                        handedness_str = results.multi_handedness[idx].classification[0].label
                    
                    self.current_landmarks.append((hand_lms, handedness_str))

                    if draw:
                        self._draw_landmarks_custom(img, hand_lms)
                    if draw_box:
                        self._draw_box_custom(img, hand_lms, handedness_str, idx)

        return img

    def _draw_landmarks_custom(self, img, hand_lms):
        h, w, _ = img.shape
        for p1_idx, p2_idx in HAND_CONNECTIONS:
            p1 = hand_lms[p1_idx] if self.use_tasks_api else hand_lms.landmark[p1_idx]
            p2 = hand_lms[p2_idx] if self.use_tasks_api else hand_lms.landmark[p2_idx]

            cx1, cy1 = int(p1.x * w), int(p1.y * h)
            cx2, cy2 = int(p2.x * w), int(p2.y * h)
            cv2.line(img, (cx1, cy1), (cx2, cy2), (255, 180, 0), 2)

        lms_iter = hand_lms if self.use_tasks_api else hand_lms.landmark
        for idx, lm in enumerate(lms_iter):
            cx, cy = int(lm.x * w), int(lm.y * h)
            if idx in self.tip_ids:
                cv2.circle(img, (cx, cy), 9, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (cx, cy), 11, (255, 255, 255), 2)
            else:
                cv2.circle(img, (cx, cy), 5, (0, 255, 255), cv2.FILLED)

    def _draw_box_custom(self, img, hand_lms, handedness_str, hand_idx):
        h, w, _ = img.shape
        lms_iter = hand_lms if self.use_tasks_api else hand_lms.landmark
        x_list = [int(lm.x * w) for lm in lms_iter]
        y_list = [int(lm.y * h) for lm in lms_iter]

        xmin, xmax = min(x_list), max(x_list)
        ymin, ymax = min(y_list), max(y_list)

        margin = 20
        xmin, ymin = max(0, xmin - margin), max(0, ymin - margin)
        xmax, ymax = min(w, xmax + margin), min(h, ymax + margin)

        label = "Tangan Kanan" if handedness_str == "Right" else "Tangan Kiri"

        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 255, 128), 2)
        cv2.rectangle(img, (xmin, ymin - 30), (xmin + 130, ymin), (0, 255, 128), cv2.FILLED)
        cv2.putText(img, label, (xmin + 8, ymin - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    def find_positions(self, img, hand_no=0, draw=True):
        lm_list = []
        if hand_no < len(self.current_landmarks):
            hand_lms, _ = self.current_landmarks[hand_no]
            h, w, _ = img.shape
            lms_iter = hand_lms if self.use_tasks_api else hand_lms.landmark

            for id, lm in enumerate(lms_iter):
                cx, cy, cz = int(lm.x * w), int(lm.y * h), round(lm.z, 4)
                lm_list.append([id, cx, cy, cz])
                if draw and id in self.tip_ids:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 255), cv2.FILLED)
        return lm_list

    def get_hand_type(self, hand_no=0):
        if hand_no < len(self.current_landmarks):
            _, handedness_str = self.current_landmarks[hand_no]
            return "Tangan Kanan" if handedness_str == "Right" else "Tangan Kiri"
        return "Tangan"

    def fingers_up(self, lm_list, hand_type="Tangan Kanan"):
        fingers = []
        if len(lm_list) == 0:
            return [0, 0, 0, 0, 0]

        if hand_type == "Tangan Kanan":
            if lm_list[self.tip_ids[0]][1] < lm_list[self.tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if lm_list[self.tip_ids[0]][1] > lm_list[self.tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        for id in range(1, 5):
            if lm_list[self.tip_ids[id]][2] < lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def find_distance(self, p1, p2, img, lm_list, draw=True, r=12, t=3):
        if len(lm_list) <= max(p1, p2):
            return 0, img, [0, 0, 0, 0, 0, 0]

        x1, y1 = lm_list[p1][1], lm_list[p1][2]
        x2, y2 = lm_list[p2][1], lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            color_mid = (0, 255, 0) if length < 30 else (0, 165, 255)
            cv2.circle(img, (cx, cy), r, color_mid, cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]
