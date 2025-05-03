import socket
import threading

import pyaudio
import time


class AudioThread(threading.Thread):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None
        self.running = False
        self.p = pyaudio.PyAudio()

    def run(self):
        """Запуск работы потока."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Устанавливаем соединение с сервером
            self.client_socket.connect((self.server_ip, self.server_port))
            print("Audio client connected to server")

            # Параметры записи (16 бит, моно, частота 44100)
            self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=44100,
                                      input=True,
                                      frames_per_buffer=1024)

            while self.running:
                # Чтение данных из микрофона
                data = self.stream.read(1024)

                # Отправка аудио данных через сокет
                self.send_audio_data(data)

                # Добавим паузу, чтобы не перегружать процесс
                time.sleep(0.05)

        except socket.error as e:
            print(f"Audio thread socket error: {e}")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            self.close_socket()

    def send_audio_data(self, data):
        """Отправка аудио данных через сокет."""
        try:
            self.client_socket.sendall(data)
            print("Sent audio data chunk")
        except socket.error as e:
            print(f"Error sending audio data: {e}")

    def close_socket(self):
        """Закрытие сокета при завершении работы потока."""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        if hasattr(self, "stream"):
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def stop(self):
        """Остановка потока."""
        self.running = False
