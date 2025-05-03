import socket
import threading

class ServerThread(threading.Thread):
    def __init__(self, client_socket, client_address):
        super().__init__()
        self.client_socket = client_socket
        self.client_address = client_address

    def run(self):
        try:
            while True:
                data = self.client_socket.recv(1024)  # Чтение данных от клиента
                if not data:
                    break

                # Пример: проверка типа данных
                if data.startswith(b"audio:"):
                    # Обрабатываем аудио данные
                    audio_data = data[6:]  # Отделяем метку от данных
                    self.process_audio(audio_data)

                elif data.startswith(b"message:"):
                    # Обрабатываем текстовое сообщение
                    message_data = data[8:]  # Отделяем метку от сообщения
                    self.process_message(message_data)

        except Exception as e:
            print(f"Ошибка сервера: {e}")
        finally:
            self.client_socket.close()

    def process_audio(self, audio_data):
        # Тут можно проигрывать или записывать аудио
        print(f"Получены аудио данные: {len(audio_data)} байт")

    def process_message(self, message_data):
        message = message_data.decode('utf-8')
        print(f"Получено сообщение: {message}")

def start_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(5)
    print(f"Сервер запущен на {ip}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Подключился клиент: {client_address}")
        server_thread = ServerThread(client_socket, client_address)
        server_thread.start()

if __name__ == "__main__":
    start_server("0.0.0.0", 5000)  # Сервер слушает на порту 5000
