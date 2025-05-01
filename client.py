import socket
import threading
import pyaudio
import mss
import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

VOICE_PORT = 50008  # Порт для аудио
VIDEO_PORT = 60001  # Порт для видео

def check_port_available(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('localhost', port))
    except socket.error:
        return False
    finally:
        s.close()
    return True

class VoiceScreenClient:
    def __init__(self, server_ip, video_label=None, video_port=60001, voice_port=50008):
        self.server_ip = server_ip
        self.video_label = video_label
        self.voice_port = voice_port
        self.video_port = video_port
        self.audio = pyaudio.PyAudio()
        self.sock_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True
        self.threads = []

    def start(self, stream_screen=False, watch_screen=False):
        t1 = threading.Thread(target=self.send_voice, daemon=True)
        t2 = threading.Thread(target=self.receive_voice, daemon=True)
        self.threads.append(t1)
        self.threads.append(t2)
        t1.start()
        t2.start()

        if stream_screen:
            t3 = threading.Thread(target=self.stream_screen, daemon=True)
            self.threads.append(t3)
            t3.start()

        if watch_screen:
            t4 = threading.Thread(target=self.receive_screen, daemon=True)
            self.threads.append(t4)
            t4.start()

    def stop(self):
        self.running = False
        for thread in self.threads:
            thread.join()
        self.sock_voice.close()
        self.sock_video_send.close()
        self.sock_video_recv.close()

    def send_voice(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        while self.running:
            data = stream.read(CHUNK, exception_on_overflow=False)
            self.sock_voice.sendto(data, (self.server_ip, self.voice_port))

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
                    chunk = data[i:i + 1024]
                    self.sock_video_send.sendto(chunk, (self.server_ip, self.video_port))
                time.sleep(1 / 15)

    def receive_screen(self):
        try:
            self.sock_video_recv.bind(('', self.video_port))
        except OSError as e:
            print(f"❌ Не удалось привязать порт: {e}")
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
                        print("✅ Получен кадр")
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image = Image.fromarray(frame)
                        imgtk = ImageTk.PhotoImage(image=image)
                        self.video_label.imgtk = imgtk
                        self.video_label.config(image=imgtk)
                    buffer = b""
            except Exception as e:
                print("❌ Ошибка видео:", e)
                break

class App:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.client_running = False
        self.build_gui()

    def build_gui(self):
        self.root.title("Голос и экран клиент")
        self.root.geometry("700x500")

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

        self.video_frame = tk.Frame(self.root, bd=5, relief=tk.SUNKEN)
        self.video_frame.pack(pady=10, padx=10)

        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack()

    def start_client(self):
        if self.client_running:
            messagebox.showinfo("Уже работает", "Клиент уже запущен")
            return

        ip = self.ip_entry.get()
        if not ip:
            messagebox.showerror("Ошибка", "Введите IP сервера")
            return

        if not check_port_available(50008):
            messagebox.showerror("Ошибка", "Порт для аудио уже занят")
            return

        if not check_port_available(60001):
            messagebox.showerror("Ошибка", "Порт для видео уже занят")
            return

        self.client = VoiceScreenClient(
            ip,
            video_label=self.video_label,
            video_port=60001,
            voice_port=50008
        )
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
