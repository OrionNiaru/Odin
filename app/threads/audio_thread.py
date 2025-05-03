import socket
import threading
import time


class AudioThread(threading.Thread):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None
        self.running = True  # Изначально поток будет работать

    def run(self):
        """Запуск работы потока."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Устанавливаем соединение с сервером
            self.client_socket.connect((self.server_ip, self.server_port))
            print("Audio client connected to server")

            while self.running:
                # Здесь вставьте код для записи и отправки аудио
                data = b"Example audio chunk"  # Пример данных
                self.send_audio_data(data)
                # Можно добавить паузу, чтобы не перегружать процесс
                time.sleep(0.5)

        except socket.error as e:
            print(f"Audio thread socket error: {e}")
        finally:
            self.close_socket()

    def send_audio_data(self, data):
        """Отправка аудио данных на сервер."""
        try:
            self.client_socket.sendall(data)
        except socket.error as e:
            print(f"Error sending audio data: {e}")
            self.close_socket()

    def close_socket(self):
        """Закрытие сокета при завершении работы потока."""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("Socket closed.")

    def stop(self):
        """Остановка потока."""
        self.running = False
        self.close_socket()
        print("Audio thread stopped.")
