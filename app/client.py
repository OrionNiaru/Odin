import pyaudio
import socket
import threading
import numpy as np
import time
import mss
import cv2

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
        self.chat_callback = chat_callback
        self.video_callback = video_callback
        self.muted = False
        self.stream_screen = stream_screen
        self.watch_screen = watch_screen
        self.running = True
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.send_voice, daemon=True).start()
        threading.Thread(target=self.receive_voice, daemon=True).start()
        threading.Thread(target=self.receive_chat, daemon=True).start()

        if self.stream_screen:
            threading.Thread(target=self.send_screen, daemon=True).start()
        if self.watch_screen:
            threading.Thread(target=self.receive_screen, daemon=True).start()

    def stop(self):
        with self.lock:
            if not self.running:
                return
            self.running = False
            self.close_sockets()

    def close_sockets(self):
        """Закрывает сокеты после завершения работы."""
        try:
            if self.sock_chat:
                self.sock_chat.close()
            if self.sock_video:
                self.sock_video.close()
            if self.sock_video_recv:
                self.sock_video_recv.close()
            if self.sock_voice:
                self.sock_voice.close()
        except Exception as e:
            print(f"Ошибка при закрытии сокетов: {e}")

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

    def send_voice(self):
        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100,
                                     input=True, frames_per_buffer=1024)
        except Exception as e:
            print(f"Ошибка микрофона: {e}")
            return

        while self.running:
            try:
                data = stream.read(1024)
                if not self.muted:
                    with self.lock:
                        self.sock_voice.sendto(data, (self.ip, VOICE_PORT))
            except Exception as e:
                print(f"Ошибка при отправке голоса: {e}")
                break

    def receive_voice(self):
        try:
            self.sock_voice.bind(('', VOICE_PORT))
            self.sock_voice.settimeout(1.0)
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100,
                                     output=True, frames_per_buffer=1024)
            while self.running:
                try:
                    data, _ = self.sock_voice.recvfrom(2048)
                    stream.write(data)
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.running:
                        print(f"[VOICE recvfrom] Ошибка: {e}")
                    break
        except Exception as e:
            print(f"Ошибка при получении голоса: {e}")

    def receive_chat(self):
        self.sock_chat.settimeout(1.0)
        while self.running:
            try:
                data, _ = self.sock_chat.recvfrom(1024)
                self.chat_callback(data.decode("utf-8"))
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    print(f"[CHAT recvfrom] Ошибка: {e}")
                break
            except Exception as e:
                print(f"Ошибка при получении чата: {e}")

    def send_chat_message(self, message):
        msg = f"[🐾 {self.nickname}]: {message}"
        try:
            with self.lock:
                self.sock_chat.sendto(msg.encode("utf-8"), (self.ip, CHAT_PORT))
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")

    def send_screen(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.running:
                try:
                    # Захват экрана
                    img = np.array(sct.grab(monitor))
                    # Увеличим размер изображения для улучшенного качества
                    frame = cv2.resize(img, (640, 360))
                    _, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

                    # Отправка данных
                    for i in range(0, len(encoded), 1024):
                        with self.lock:
                            self.sock_video.sendto(encoded[i:i + 1024], (self.ip, VIDEO_PORT))

                    # Пауза для стабилизации потока
                    time.sleep(1 / 20)  # Увеличим частоту кадров

                except Exception as e:
                    print(f"Ошибка при трансляции экрана: {e}")
                    break

    def receive_screen(self):
        buffer = b""  # Буфер для сборки данных
        try:
            self.sock_video_recv.bind(('', VIDEO_PORT))
            self.sock_video_recv.settimeout(1.0)  # Таймаут для сокета
            while self.running:
                try:
                    chunk, _ = self.sock_video_recv.recvfrom(1024)
                    buffer += chunk  # Добавляем новый кусок в буфер

                    # Когда в буфере накопилось достаточно данных для одного изображения
                    if len(buffer) > 10000:  # Пороговое значение для изображения
                        frame = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            # Вставляем кадр в окно видео
                            self.video_callback(frame)
                        buffer = b""  # Очистить буфер после обработки
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.running:
                        print(f"[VIDEO recvfrom] Ошибка: {e}")
                    break
        except Exception as e:
            print(f"Ошибка при получении экрана: {e}")


