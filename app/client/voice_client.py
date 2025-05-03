import socket
import threading
import pyaudio
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

class VoiceClient:
    def __init__(self, ip, nickname, chat_callback, video_callback, stream_screen=False, watch_screen=False):
        self.ip = ip
        self.nickname = nickname
        self.audio = pyaudio.PyAudio()
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
                        self.video_callback(frame)
                    buffer = b""
            except: break
