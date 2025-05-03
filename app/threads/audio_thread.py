import pyaudio
import threading
import socket
import numpy as np
from PyQt5.QtCore import pyqtSignal, QThread

class AudioThread(QThread):
    audio_received = pyqtSignal(np.ndarray)  # Сигнал для передачи аудио в основной поток

    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = True
        self.audio_socket = None
        self.p = pyaudio.PyAudio()

        # Настройки для захвата аудио
        self.chunk_size = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100

    def run(self):
        try:
            # Настройка потока для записи аудио
            stream = self.p.open(format=self.sample_format,
                                 channels=self.channels,
                                 rate=self.rate,
                                 input=True,
                                 frames_per_buffer=self.chunk_size)
            self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.audio_socket.connect((self.server_ip, self.server_port))
            print("Audio stream started.")

            while self.running:
                # Чтение аудио данных с микрофона
                audio_data = stream.read(self.chunk_size)

                # Отправляем данные на сервер
                self.audio_socket.send(audio_data)

                # Отправляем сигнал в основной поток для обработки
                self.audio_received.emit(np.frombuffer(audio_data, dtype=np.int16))

        except Exception as e:
            print(f"Ошибка в потоке AudioThread: {e}")

    def stop(self):
        self.running = False
        self.audio_socket.close()
        self.p.terminate()
        print("Audio stream stopped.")


class AudioReceiverThread(QThread):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = True
        self.p = pyaudio.PyAudio()

        # Настройки для воспроизведения аудио
        self.chunk_size = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100

    def run(self):
        try:
            # Настройка потока для воспроизведения аудио
            stream = self.p.open(format=self.sample_format,
                                 channels=self.channels,
                                 rate=self.rate,
                                 output=True,
                                 frames_per_buffer=self.chunk_size)

            audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            audio_socket.bind((self.server_ip, self.server_port))
            print("Audio receiver started.")

            while self.running:
                # Получаем данные с сервера
                audio_data, _ = audio_socket.recvfrom(self.chunk_size)

                # Воспроизводим аудио
                stream.write(audio_data)

        except Exception as e:
            print(f"Ошибка в потоке AudioReceiverThread: {e}")

    def stop(self):
        self.running = False
        self.p.terminate()
        print("Audio receiver stopped.")

