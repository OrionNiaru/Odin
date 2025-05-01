import socket
import threading
import pyaudio
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
import numpy as np
import mss
import cv2
import io

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
VOICE_PORT = 50007
CHAT_PORT = 50008
VIDEO_PORT = 60000
SETTINGS_FILE = "settings.json"

class VoiceClient:
    def __init__(self, ip, nickname, device_index, chat_callback, video_callback, stream_screen=False, watch_screen=False):
        self.ip = ip
        self.nickname = nickname
        self.device_index = device_index
        self.audio = pyaudio.PyAudio()
        self.sock_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_chat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_chat.bind(('', 0))
        self.sock_video_recv.bind(('', 0))
        self.chat_callback = chat_callback
        self.video_callback = video_callback
        self.running = True
        self.muted = False
        self.stream_screen = stream_screen
        self.watch_screen = watch_screen

    def start(self):
        try:
            self.sock_chat.sendto(b"REGISTER", (self.ip, CHAT_PORT))
            print("🐾 REGISTER отправлен на чат-сервер")
        except Exception as e:
            print("❌ Ошибка регистрации чата:", e)

        threading.Thread(target=self.send_voice, daemon=True).start()
        threading.Thread(target=self.receive_voice, daemon=True).start()
        threading.Thread(target=self.receive_chat, daemon=True).start()

        if self.stream_screen:
            threading.Thread(target=self.send_screen, daemon=True).start()
        if self.watch_screen:
            threading.Thread(target=self.receive_screen, daemon=True).start()

    def stop(self):
        self.running = False
        try:
            self.sock_chat.sendto(b"UNREGISTER", (self.ip, CHAT_PORT))
        except:
            pass
        self.sock_voice.close()
        self.sock_chat.close()
        self.sock_video.close()
        self.sock_video_recv.close()

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

    def send_voice(self):
        try:
            stream = self.audio.open(
                format=FORMAT, channels=CHANNELS, rate=RATE,
                input=True, frames_per_buffer=CHUNK,
                input_device_index=self.device_index
            )
        except Exception as e:
            print(f"❌ Ошибка микрофона: {e}")
            return

        while self.running:
            data = stream.read(CHUNK, exception_on_overflow=False)
            if not self.muted:
                self.sock_voice.sendto(data, (self.ip, VOICE_PORT))

    def receive_voice(self):
        stream = self.audio.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            output=True, frames_per_buffer=CHUNK)
        self.sock_voice.bind(('', 0))
        while self.running:
            try:
                data, _ = self.sock_voice.recvfrom(2048)
                stream.write(data)
            except:
                break

    def receive_chat(self):
        while self.running:
            try:
                data, _ = self.sock_chat.recvfrom(1024)
                self.chat_callback(data.decode('utf-8'))
            except:
                break

    def send_chat_message(self, message):
        full_msg = f"[🐾 {self.nickname}]: {message}"
        self.sock_chat.sendto(full_msg.encode('utf-8'), (self.ip, CHAT_PORT))

    def send_screen(self):
        import time
        target_fps = 1  # 🎯 Частота кадров
        quality = 50  # 🖼️ JPEG качество (1–100)
        width, height = 640, 360  # 📐 Разрешение

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            last_time = time.time()

            while self.running:
                start = time.time()
                img = np.array(sct.grab(monitor))
                frame = cv2.resize(img, (width, height))

                _, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                data = encoded.tobytes()

                for i in range(0, len(data), 1024):
                    self.sock_video.sendto(data[i:i + 1024], (self.ip, VIDEO_PORT))

                # 💡 Вывод FPS
                end = time.time()
                elapsed = end - start
                fps = 1 / elapsed if elapsed > 0 else 0
                print(f"📺 Стрим экрана: {fps:.1f} FPS, {width}x{height}")

                # Ограничение частоты кадров
                delay = max(0, 1 / target_fps - elapsed)
                time.sleep(delay)

    def receive_screen(self):
        self.sock_video_recv.bind(('', VIDEO_PORT))
        buffer = b""
        while self.running:
            try:
                chunk, _ = self.sock_video_recv.recvfrom(1024)
                buffer += chunk
                if len(buffer) > 20000:
                    frame = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        self.video_callback(img)
                    buffer = b""
            except Exception as e:
                print("❌ Ошибка при приёме экрана:", e)

class App:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.audio = pyaudio.PyAudio()
        self.root.title("🐾 Кото-чат с экранчиком")
        self.root.geometry("800x520")
        self.build_gui()
        self.load_settings()

    def build_gui(self):
        style = ttk.Style()
        style.configure("TFrame", background="#ffe6f0")
        style.configure("TLabel", background="#ffe6f0", font=("Comic Sans MS", 10))
        style.configure("TButton", font=("Comic Sans MS", 10))
        style.configure("TEntry", font=("Comic Sans MS", 10))
        style.configure("TCombobox", font=("Comic Sans MS", 10))

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(main)
        left.pack(side="left", fill="y", expand=False)

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="IP сервера:").pack()
        self.ip_entry = ttk.Entry(left)
        self.ip_entry.pack()

        ttk.Label(left, text="Ник:").pack()
        self.name_entry = ttk.Entry(left)
        self.name_entry.pack()

        ttk.Label(left, text="Микрофон:").pack()
        self.device_var = tk.StringVar()
        self.device_menu = ttk.Combobox(left, textvariable=self.device_var, state="readonly")
        self.device_menu.pack()
        self.populate_devices()

        self.stream_screen_var = tk.BooleanVar()
        self.watch_screen_var = tk.BooleanVar()
        ttk.Checkbutton(left, text="Транслировать экран", variable=self.stream_screen_var).pack()
        ttk.Checkbutton(left, text="Смотреть экран", variable=self.watch_screen_var).pack()

        self.status_label = ttk.Label(left, text="🔴 Отключён")
        self.status_label.pack(pady=5)

        btns = ttk.Frame(left)
        btns.pack(pady=5)
        self.start_btn = ttk.Button(btns, text="Запуск", command=self.start_client)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(btns, text="Стоп", command=self.stop_client, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        self.mute_btn = ttk.Button(btns, text="Mute", command=self.toggle_mute, state="disabled")
        self.mute_btn.pack(side="left", padx=5)

        # Экран
        self.video_label = ttk.Label(right)
        self.video_label.pack(pady=5)

        # Чат
        self.chat_box = tk.Text(right, state="disabled", wrap="word", height=12)
        self.chat_box.pack(fill="both", expand=True)

        chat_frame = ttk.Frame(right)
        chat_frame.pack(fill="x", pady=5)
        self.chat_entry = ttk.Entry(chat_frame)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.send_btn = ttk.Button(chat_frame, text="Отправить", command=self.send_chat)
        self.send_btn.pack(side="right", padx=5)

    def populate_devices(self):
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                try:
                    name = info["name"].encode("latin1").decode("utf-8")
                except:
                    name = info["name"]
                devices.append(f"{name} (#{i})")
        self.device_menu["values"] = devices
        if devices:
            self.device_menu.current(0)

    def chat_log(self, message):
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", f"{message}")
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")

    def update_video(self, img):
        img_tk = ImageTk.PhotoImage(img)
        self.video_label.configure(image=img_tk)
        self.video_label.image = img_tk

    def start_client(self):
        ip = self.ip_entry.get().strip()
        nickname = self.name_entry.get().strip() or "Котик"
        device_index = int(self.device_menu.get().split("#")[-1].replace(")", "").strip())
        self.client = VoiceClient(
            ip, nickname, device_index,
            chat_callback=self.chat_log,
            video_callback=self.update_video,
            stream_screen=self.stream_screen_var.get(),
            watch_screen=self.watch_screen_var.get()
        )
        self.client.start()
        self.status_label.config(text=f"🟢 Подключён как {nickname}")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.mute_btn.config(state="normal")
        self.save_settings()

    def stop_client(self):
        if self.client:
            self.client.stop()
            self.client = None
        self.status_label.config(text="🔴 Отключён")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.mute_btn.config(state="disabled")

    def toggle_mute(self):
        if self.client:
            muted = self.client.toggle_mute()
            self.mute_btn.config(text="Unmute" if muted else "Mute")
            self.chat_log("🔇 Микрофон выключен" if muted else "🎤 Микрофон включен")

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        if msg and self.client:
            self.client.send_chat_message(msg)
            self.chat_log(f"[🐾 {self.client.nickname}]: {msg}")
            self.chat_entry.delete(0, tk.END)

    def save_settings(self):
        settings = {
            "ip": self.ip_entry.get(),
            "nickname": self.name_entry.get(),
            "device": self.device_menu.get()
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.ip_entry.insert(0, settings.get("ip", ""))
                self.name_entry.insert(0, settings.get("nickname", ""))
                device = settings.get("device", "")
                if device in self.device_menu["values"]:
                    self.device_menu.set(device)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()