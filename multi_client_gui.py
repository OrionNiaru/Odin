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
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.running:
                img = np.array(sct.grab(monitor))
                frame = cv2.resize(img, (640, 360))
                _, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                data = encoded.tobytes()
                for i in range(0, len(data), 1024):
                    chunk = data[i:i+1024]
                    self.sock_video_send.sendto(chunk, (self.server_ip, VIDEO_PORT))
                time.sleep(1/15)

    def receive_screen(self):
        try:
            self.sock_video_recv.bind(('', VIDEO_PORT))
        except OSError as e:
            print(f"❌ Не удалось привязать порт {VIDEO_PORT}: {e}")
            return

        buffer = b""
        print("▶️ Ожидаем кадры с экрана...")
        while self.running:
            try:
                chunk, _ = self.sock_video_recv.recvfrom(1024)
                buffer += chunk
                if len(buffer) > 50000:
                    frame = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow("📺 Экран", frame)
                        if cv2.waitKey(1) == 27:
                            break
                    buffer = b""
            except Exception as e:
                print("❌ Ошибка видео:", e)
                break
        cv2.destroyAllWindows()

    def stop(self):
        self.running = False


class App:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.client_running = False
        self.build_gui()

    def build_gui(self):
        self.root.title("Голос и экран клиент")
        self.root.geometry("300x250")

        tk.Label(self.root, text="IP сервера:").pack(pady=5)
        self.ip_entry = tk.Entry(self.root)
        self.ip_entry.pack()
        self.ip_entry.insert(0, "127.0.0.1")

        self.voice_var = tk.BooleanVar(value=True)
        self.screen_send_var = tk.BooleanVar()
        self.screen_recv_var = tk.BooleanVar()

        tk.Checkbutton(self.root, text="Транслировать экран", variable=self.screen_send_var).pack()
        tk.Checkbutton(self.root, text="Смотреть экран", variable=self.screen_recv_var).pack()

        self.start_btn = tk.Button(self.root, text="Запустить", command=self.start_client)
        self.start_btn.pack(pady=10)

        self.stop_btn = tk.Button(self.root, text="Остановить", command=self.stop_client, state=tk.DISABLED)
        self.stop_btn.pack()

    def start_client(self):
        if self.client_running:
            messagebox.showinfo("Уже работает", "Клиент уже запущен")
            return

        ip = self.ip_entry.get()
        if not ip:
            messagebox.showerror("Ошибка", "Введите IP сервера")
            return

        self.client = VoiceScreenClient(ip)
        self.client.start(
            stream_screen=self.screen_send_var.get(),
            watch_screen=self.screen_recv_var.get()
        )
        self.client_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_client(self):
        if self.client:
            self.client.stop()
        self.client_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
