"""
Demo Minimalist Hand Tracking (MediaPipe + OpenCV)
File ini dirancang simpel untuk pengujian dasar pada seluruh versi MediaPipe & Python 3.13.
"""
import cv2
import mediapipe as mp
from hand_tracking_module import HandDetector

# 1. Inisialisasi HandDetector
detector = HandDetector(max_hands=2, detection_con=0.5)

# 2. Buka Webcam
cap = cv2.VideoCapture(0)

print("[INFO] Membuka webcam... Tekan 'q' pada jendela video untuk keluar.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Mirroring gambar
    frame = cv2.flip(frame, 1)

    # 3. Deteksi Tangan & Gambar Landmark
    frame = detector.find_hands(frame, draw=True, draw_box=True)

    # 4. Tampilkan Jendela Video
    cv2.imshow("Hand Tracker Simple Demo", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
