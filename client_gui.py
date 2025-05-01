import socket
import threading
import pyaudio
import tkinter as tk
from tkinter import ttk, messagebox
import json

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
VOICE_PORT = 50007
CHAT_PORT = 50008
SETTINGS_FILE = "settings.json"

class VoiceClient:
    def __init__(self, ip, nickname, device_index, chat_callback):
        self.ip = ip
        self.nickname = nickname
        self.device_index = device_index
        self.audio = pyaudio.PyAudio()
        self.sock_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_chat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_chat.bind(('', 0))
        self.chat_callback = chat_callback
        self.running = True
        self.muted = False

    def start(self):
        # 👇 Отправим REGISTER на чат-сервер
        try:
            self.sock_chat.sendto(b"REGISTER", (self.ip, CHAT_PORT))
            print("🐾 REGISTER отправлен на чат-сервер")
        except Exception as e:
            print("❌Ошибка регистрации чата:", e)
        threading.Thread(target=self.receive_chat, daemon=True).start()
        # try:
        #     threading.Thread(target=self.send_voice, daemon=True).start()
        #     threading.Thread(target=self.receive_voice, daemon=True).start()
        # except Exception as e:
        #     print("❌Ошибка обработки аудио", e)


    def stop(self):
        self.running = False
        self.sock_voice.close()
        self.sock_chat.close()

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

    def send_voice(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                 input=True, frames_per_buffer=CHUNK, input_device_index=self.device_index)
        while self.running:
            data = stream.read(CHUNK, exception_on_overflow=False)
            if not self.muted:
                self.sock_voice.sendto(data, (self.ip, VOICE_PORT))

    def receive_voice(self):
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
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
        print(f"📤 Отправка чата: {full_msg}")  # 👈 лог в консоль
        self.sock_chat.sendto(full_msg.encode('utf-8'), (self.ip, CHAT_PORT))



class App:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.audio = pyaudio.PyAudio()
        self.root.title("🐾 Кото-Чат UwU")
        self.root.geometry("720x420")
        self.build_gui()
        self.load_settings()

    def build_gui(self):
        style = ttk.Style()
        style.configure("TFrame", background="#ffe6f0")
        style.configure("TLabel", background="#ffe6f0", font=("Comic Sans MS", 10))
        style.configure("TButton", font=("Comic Sans MS", 10))
        style.configure("TEntry", font=("Comic Sans MS", 10))
        style.configure("TCombobox", font=("Comic Sans MS", 10))

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(main_frame)
        left.pack(side="left", fill="both", expand=True)

        right = ttk.Frame(main_frame)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="IP сервера:").pack()
        self.ip_entry = ttk.Entry(left)
        self.ip_entry.pack()

        ttk.Label(left, text="Никнейм:").pack()
        self.name_entry = ttk.Entry(left)
        self.name_entry.pack()

        ttk.Label(left, text="Микрофон:").pack()
        self.device_var = tk.StringVar()
        self.device_menu = ttk.Combobox(left, textvariable=self.device_var, state="readonly")
        self.device_menu.pack()
        self.populate_devices()

        self.status_label = ttk.Label(left, text="🔴 Отключён")
        self.status_label.pack(pady=5)

        self.log_box = tk.Text(left, height=6, state="disabled", font=("Courier", 9))
        self.log_box.pack(fill="x", pady=5)

        btns = ttk.Frame(left)
        btns.pack(pady=5)
        self.start_btn = ttk.Button(btns, text="Запуск", command=self.start_client)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(btns, text="Стоп", command=self.stop_client, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        self.mute_btn = ttk.Button(btns, text="🔇 Mute", command=self.toggle_mute, state="disabled")
        self.mute_btn.pack(side="left", padx=5)

        # 🐾 Чат
        ttk.Label(right, text="Общий чат 🐱").pack()
        self.chat_box = tk.Text(right, state="disabled", wrap="word", height=15, font=("Comic Sans MS", 10))
        self.chat_box.pack(fill="both", expand=True)

        chat_entry_frame = ttk.Frame(right)
        chat_entry_frame.pack(fill="x", pady=5)
        self.chat_entry = ttk.Entry(chat_entry_frame)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.send_btn = ttk.Button(chat_entry_frame, text="Отправить", command=self.send_chat)
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

    def log(self, message):
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def chat_log(self, message):
        self.chat_box.config(state="normal")
        self.chat_box.insert("end", f"{message}\n")
        self.chat_box.see("end")
        self.chat_box.config(state="disabled")

    def start_client(self):
        if self.client:
            self.log("Клиент уже запущен.")
            return

        ip = self.ip_entry.get().strip()
        nickname = self.name_entry.get().strip() or "Котик"
        device_index = int(self.device_menu.get().split("#")[-1][:-1])

        self.client = VoiceClient(ip, nickname, device_index, self.chat_log)
        self.client.start()
        self.status_label.config(text=f"🟢 Подключён как {nickname}")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.mute_btn.config(state="normal")
        self.log(f"Подключение к {ip} как {nickname}")
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
            self.mute_btn.config(text="🔊 Unmute" if muted else "🔇 Mute")
            self.log("🎙 Микрофон выключен" if muted else "🎤 Микрофон включен")

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        self.chat_log(f"[🐾 {self.client.nickname}]: {msg}")  # 👈 покажем своё сообщение
        if msg and self.client:
            self.client.send_chat_message(msg)
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
