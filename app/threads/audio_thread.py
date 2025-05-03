import socket
import time
import pyaudio
from PyQt5.QtCore import QThread

class AudioThread(QThread):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = True
        self.client_socket = None

        # Инициализация PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = None

    def run(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            print("Audio client connected to server")

            # Настройка для записи аудио
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=44100,
                                      input=True,
                                      frames_per_buffer=1024)

            while self.running:
                data = self.stream.read(1024)  # Чтение аудио данных
                self.send_audio_data(data)  # Отправка данных на сервер
                time.sleep(0.1)

        except Exception as e:
            print(f"Ошибка в аудио потоке: {e}")

    def send_audio_data(self, data):
        try:
            self.client_socket.sendall(data)  # Отправляем аудио данные
        except Exception as e:
            print(f"Ошибка отправки данных: {e}")

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.client_socket:
            self.client_socket.close()
