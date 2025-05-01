import socket
import threading
import pyaudio
import mss
import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import messagebox

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

VOICE_PORT = 50007
VIDEO_PORT = 60000

class VoiceScreenClient:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.audio = pyaudio.PyAudio()
        self.sock_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True

    def start(self, stream_screen=False, watch_screen=False):
        threading.Thread(target=self.send_voice, daemon=True).start()
        threading.Thread(target=self.receive_voice, daemon=True).start()
        if stream_screen:
            threading.Thread(target=self.stream_screen, daemon=True).start()
        if watch_screen:
            threading.Thread(target=self.receive_screen, daemon=True).start()

    def send_voice(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        while self.running:
            data = stream.read(CHUNK, exception_on_overflow=False)
            self.sock_voice.sendto(data, (self.server_ip, VOICE_PORT))

    def receive_voice(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        self.sock_voice.bind(('', 0))
        while self.running:
            data, _ = self.sock_voice.recvfrom(2048)
            stream.write(data)

    def stream_screen(self):
        print("🟢 Начата трансляция экрана")
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.running:
                img = np.array(sct.grab(monitor))
                frame = cv2.resize(img, (640, 360))
                _, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                data = encoded.tobytes()

                frame_len = len(data)
                header = frame_len.to_bytes(4, 'big')  # 4-байтный заголовок
                packet = header + data

                for i in range(0, len(packet), 1024):
                    chunk = packet[i:i+1024]
                    self.sock_video_send.sendto(chunk, (self.server_ip, VIDEO_PORT))

                time.sleep(1 / 15)

    def receive_screen(self):
        try:
            self.sock_video_recv.bind(('', VIDEO_PORT))
        except OSError as e:
            print(f"❌ Не удалось привязать порт {VIDEO_PORT}: {e}")
            return

        print("▶️ Ожидаем кадры с экрана...")
        buffer = b""
        expected_size = None

        while self.running:
            try:
                chunk, _ = self.sock_video_recv.recvfrom(1024)
                buffer += chunk

                if expected_size is None and len(buffer) >= 4:
                    expected_size = int.from_bytes(buffer[:4], 'big')
                    buffer = buffer[4:]

                if expected_size is not None and len(buffer) >= expected_size:
                    frame_data = buffer[:expected_size]
                    buffer = buffer[expected_size:]
                    expected_size = None

                    frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow("📺 Экран", frame)
                        if cv2.waitKey(1) == 27:
                            break
            except Exception as e:
                print("❌ Ошибка видео:", e)
                break

        cv2.destroyAllWindows()

    def stop(self):
        self.running = False
