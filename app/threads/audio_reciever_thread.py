import socket
import threading


class AudioReceiverThread(threading.Thread):
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = True
        self.server_socket = None

    def run(self):
        try:
            # Создание UDP сокета для получения данных
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Разрешаем повторное использование порта
            self.server_socket.bind(('0.0.0.0', self.server_port))  # Прослушивание на всех интерфейсах
            print(f"Audio receiver started on {self.server_ip}:{self.server_port}")

            while self.running:
                try:
                    # Получаем данные от клиента (максимальный размер буфера 1024 байта)
                    data, addr = self.server_socket.recvfrom(1024)
                    if data:
                        print(f"Received data from {addr}: {data}")
                        # Обработка аудио данных
                        self.process_audio_data(data)
                except socket.error as e:
                    print(f"Audio receiver socket error: {e}")
                    break

        except Exception as e:
            print(f"Audio receiver error: {e}")
        finally:
            self.close_socket()

    def process_audio_data(self, data):
        """Обработка полученных аудио данных."""
        print(f"Processing audio data: {data}")
        # Здесь можно добавить логику для воспроизведения или сохранения данных

    def close_socket(self):
        """Закрытие сокета при завершении работы потока."""
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            print("Socket closed.")
