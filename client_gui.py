import socket
import threading
import pyaudio
import tkinter as tk
from tkinter import messagebox, ttk
import json

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
DEFAULT_PORT = 50007
SETTINGS_FILE = "settings.json"

class VoiceClient:
    def __init__(self, server_ip, port, nickname):
        self.server_ip = server_ip
        self.port = port
        self.nickname = nickname
        self.audio = pyaudio.PyAudio()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True
        self.muted = False

    def start(self):
        threading.Thread(target=self.send_voice, daemon=True).start()
        threading.Thread(target=self.receive_voice, daemon=True).start()

    def send_voice(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                 input=True, frames_per_buffer=CHUNK)
        while self.running:
            data = stream.read(CHUNK, exception_on_overflow=False)
            if not self.muted:
                self.sock.sendto(data, (self.server_ip, self.port))

    def receive_voice(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        self.sock.bind(('', 0))
        while self.running:
            data, _ = self.sock.recvfrom(2048)
            stream.write(data)

    def stop(self):
        self.running = False
        self.sock.close()

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

class App:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.client_running = False
        self.build_gui()
        self.load_settings()

    def build_gui(self):
        self.root.title("Голосовой чат")
        self.root.geometry("400x350")

        ttk.Label(self.root, text="IP сервера:").pack(pady=2)
        self.ip_entry = ttk.Entry(self.root)
        self.ip_entry.pack()

        ttk.Label(self.root, text="Порт:").pack(pady=2)
        self.port_entry = ttk.Entry(self.root)
        self.port_entry.pack()
        self.port_entry.insert(0, str(DEFAULT_PORT))

        ttk.Label(self.root, text="Никнейм:").pack(pady=2)
        self.name_entry = ttk.Entry(self.root)
        self.name_entry.pack()

        self.status_label = ttk.Label(self.root, text="Статус: 🔴 Отключён")
        self.status_label.pack(pady=5)

        self.log_text = tk.Text(self.root, height=8, state="disabled")
        self.log_text.pack(pady=5, padx=5, fill="both", expand=True)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        self.start_btn = ttk.Button(btn_frame, text="Запустить", command=self.start_client)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Остановить", command=self.stop_client, state=tk.DISABLED)
        self.stop_btn.pack(side="left", padx=5)

        self.mute_btn = ttk.Button(btn_frame, text="Mute", command=self.toggle_mute, state=tk.DISABLED)
        self.mute_btn.pack(side="left", padx=5)

    def start_client(self):
        if self.client_running:
            self.log("Клиент уже запущен")
            return

        ip = self.ip_entry.get().strip()
        port = int(self.port_entry.get().strip())
        nickname = self.name_entry.get().strip() or "Anonymous"

        self.client = VoiceClient(ip, port, nickname)
        self.client.start()
        self.client_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.mute_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Статус: 🟢 Подключён как {nickname}")
        self.log(f"Подключено к {ip}:{port} как {nickname}")
        self.save_settings()

    def stop_client(self):
        if self.client:
            self.client.stop()
        self.client_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.mute_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Статус: 🔴 Отключён")
        self.log("Отключение завершено")

    def toggle_mute(self):
        if self.client:
            muted = self.client.toggle_mute()
            self.mute_btn.config(text="Unmute" if muted else "Mute")
            self.log("🔇 Микрофон выключен" if muted else "🎤 Микрофон включен")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def save_settings(self):
        settings = {
            "ip": self.ip_entry.get().strip(),
            "port": self.port_entry.get().strip(),
            "nickname": self.name_entry.get().strip()
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, settings.get("ip", ""))
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, settings.get("port", str(DEFAULT_PORT)))
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, settings.get("nickname", ""))
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
