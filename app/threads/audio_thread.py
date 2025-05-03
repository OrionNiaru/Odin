import socket
import pyaudio
import time
from PyQt5.QtCore import QThread  # Импорт QThread

class AudioThread(QThread):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = True
        self.client_socket = None

    def run(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))
        print("Audio thread connected to server")

        # Инициализация PyAudio для записи
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

        while self.running:
            # Чтение аудио данных
            data = stream.read(1024)
            self.send_audio_data(data)
            time.sleep(0.1)

    def send_audio_data(self, data):
        """Метод для отправки аудио данных серверу."""
        try:
            self.client_socket.sendall(data)
        except Exception as e:
            print(f"Error sending audio data: {e}")

    def stop(self):
        """Метод для остановки потока."""
        self.running = False
        if self.client_socket:
            self.client_socket.close()
