from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import cv2
import numpy as np

try:
    import mss
except ImportError:
    mss = None

class VideoThread(QThread):
    frame_received = pyqtSignal(QImage)

    def __init__(self, watch_screen=False, use_webcam=False):
        super().__init__()
        self.watch_screen = watch_screen
        self.use_webcam = use_webcam
        self.running = True
        self.cap = None

        if not self.watch_screen and self.use_webcam:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Пробуем использовать камеру 0 (если она есть)

    def run(self):
        if self.watch_screen:
            if mss is None:
                print("mss не установлен. Установите через: pip install mss")
                return

            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Используем первый монитор
                try:
                    while self.running:
                        screenshot = np.array(sct.grab(monitor))
                        frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2RGB)
                        h, w, ch = frame.shape
                        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        self.frame_received.emit(img)
                except Exception as e:
                    print(f"Ошибка в потоке: {e}")
        elif self.use_webcam:
            if self.cap is None or not self.cap.isOpened():
                print("Не удалось открыть вебкамеру.")
                return

            try:
                while self.running:
                    ret, frame = self.cap.read()
                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = frame.shape
                        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                        self.frame_received.emit(img)
            except Exception as e:
                print(f"Ошибка в потоке: {e}")

    def stop(self):
        self.running = False
        if hasattr(self, "cap"):
            self.cap.release()
        self.quit()
        self.wait()