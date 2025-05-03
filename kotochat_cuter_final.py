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
import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
VOICE_PORT = 50007
CHAT_PORT = 50008
VIDEO_PORT = 60000
SETTINGS_FILE = "settings.json"

class VoiceClient:
    def __init__(self, ip, nickname, chat_callback, video_callback, stream_screen=False, watch_screen=False):
        self.ip = ip
        self.nickname = nickname
        self.audio = pyaudio.PyAudio()
        self.device_index = None
        self.sock_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_chat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_video_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_chat.bind(('', 0))
        self.chat_callback = chat_callback
        self.video_callback = video_callback
        self.running = True
        self.muted = False
        self.stream_screen = stream_screen
        self.watch_screen = watch_screen

    def start(self):
        try:
            self.sock_chat.sendto(b"REGISTER", (self.ip, CHAT_PORT))
        except: pass

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
        except: pass
        for sock in [self.sock_voice, self.sock_chat, self.sock_video, self.sock_video_recv]:
            try: sock.close()
            except: pass

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

    def send_voice(self):
        try:
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                     input=True, frames_per_buffer=CHUNK)
        except Exception as e:
            print("❌ Микрофон:", e)
            return
        while self.running:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                if not self.muted:
                    self.sock_voice.sendto(data, (self.ip, VOICE_PORT))
            except: break

    def receive_voice(self):
        try:
            self.sock_voice.bind(('', 0))
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                     output=True, frames_per_buffer=CHUNK)
            while self.running:
                data, _ = self.sock_voice.recvfrom(2048)
                stream.write(data)
        except: pass

    def receive_chat(self):
        while self.running:
            try:
                data, _ = self.sock_chat.recvfrom(1024)
                self.chat_callback(data.decode("utf-8") + "\n")
            except: break

    def send_chat_message(self, message):
        msg = f"[🐾 {self.nickname}]: {message}"
        try:
            self.sock_chat.sendto(msg.encode("utf-8"), (self.ip, CHAT_PORT))
        except: pass

    def send_screen(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.running:
                try:
                    img = np.array(sct.grab(monitor))
                    frame = cv2.resize(img, (320, 180))
                    _, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                    for i in range(0, len(encoded), 1024):
                        self.sock_video.sendto(encoded[i:i+1024], (self.ip, VIDEO_PORT))
                    time.sleep(1/15)
                except: break

    def receive_screen(self):
        try:
            self.sock_video_recv.bind(('', VIDEO_PORT))
        except: return
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
            except: break

class App:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.root.title("🐾 Кото-Чат UwU")
        self.root.geometry("1000x600")
        self.root.configure(bg="#fff0f5")
        self.build_gui()
        self.load_settings()
        self.root.bind("<F1>", self.hotkey_toggle_mute)

    def build_gui(self):
        style = ttk.Style()
        style.configure("TLabel", background="#fff0f5", font=("Comic Sans MS", 10))
        style.configure("TButton", font=("Comic Sans MS", 10))
        style.configure("TEntry", font=("Comic Sans MS", 10))
        style.configure("TCheckbutton", background="#fff0f5", font=("Comic Sans MS", 10))

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg="#fff0f5")
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(main, bg="#fff0f5")
        right.pack(side="right", fill="both", expand=True)

        tk.Label(left, text="IP сервера:", bg="#fff0f5").pack()
        self.ip_entry = ttk.Entry(left)
        self.ip_entry.pack()

        tk.Label(left, text="Никнейм:", bg="#fff0f5").pack()
        self.name_entry = ttk.Entry(left)
        self.name_entry.pack()

        self.stream_var = tk.BooleanVar()
        self.watch_var = tk.BooleanVar()
        ttk.Checkbutton(left, text="Транслировать экран", variable=self.stream_var).pack()
        ttk.Checkbutton(left, text="Смотреть экран", variable=self.watch_var).pack()

        self.status_label = ttk.Label(left, text="🔴 Отключён")
        self.status_label.pack()

        self.log_text = tk.Text(left, height=5, bg="#ffe6f0", font=("Consolas", 9))
        self.log_text.pack(fill="x", padx=5, pady=5)

        btns = ttk.Frame(left)
        btns.pack()
        self.start_btn = ttk.Button(btns, text="Запуск", command=self.start_client)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(btns, text="Стоп", command=self.stop_client, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        self.mute_btn = ttk.Button(btns, text="Mute (F1)", command=self.toggle_mute, state="disabled")
        self.mute_btn.pack(side="left", padx=5)

        tk.Label(right, text="Общий чат 🐾", bg="#fff0f5", font=("Comic Sans MS", 10, "bold")).pack()
        self.video_label = tk.Label(right, bg="#fff0f5")
        self.video_label.pack()

        self.chat_box = tk.Text(right, state="disabled", wrap="word", height=15, bg="#ffffff", font=("Comic Sans MS", 10))
        self.chat_box.pack(fill="both", expand=True)

        chat_frame = tk.Frame(right, bg="#fff0f5")
        chat_frame.pack(fill="x")
        self.chat_entry = ttk.Entry(chat_frame)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.send_btn = ttk.Button(chat_frame, text="Отправить", command=self.send_chat)
        self.send_btn.pack(side="right")

    def chat_log(self, message):
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", message)
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")

    def update_video(self, img):
        imgtk = ImageTk.PhotoImage(img)
        self.video_label.config(image=imgtk)
        self.video_label.image = imgtk

    def start_client(self):
        ip = self.ip_entry.get().strip()
        name = self.name_entry.get().strip() or "Котик"
        self.client = VoiceClient(ip, name, self.chat_log, self.update_video,
                                  stream_screen=self.stream_var.get(), watch_screen=self.watch_var.get())
        self.client.start()
        self.status_label.config(text=f"🟢 Подключён как {name}")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.mute_btn.config(state="normal")
        self.log("Подключение к " + ip + " как " + name)
        self.save_settings()

    def stop_client(self):
        if self.client:
            self.client.stop()
        self.client = None
        self.status_label.config(text="🔴 Отключён")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.mute_btn.config(state="disabled")
        self.log("Отключено.")

    def toggle_mute(self):
        if self.client:
            muted = self.client.toggle_mute()
            self.mute_btn.config(text="Unmute (F1)" if muted else "Mute (F1)")
            self.chat_log("🔇 Микрофон выключен\n" if muted else "🎤 Микрофон включен\n")

    def hotkey_toggle_mute(self, event):
        self.toggle_mute()

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        if msg and self.client:
            self.client.send_chat_message(msg)
            self.chat_log(f"[🐾 {self.client.nickname}]: {msg}\n")
            self.chat_entry.delete(0, tk.END)

    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "ip": self.ip_entry.get().strip(),
                    "nickname": self.name_entry.get().strip()
                }, f)
        except: pass

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                self.ip_entry.insert(0, s.get("ip", ""))
                self.name_entry.insert(0, s.get("nickname", ""))
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()