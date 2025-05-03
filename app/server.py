import socket
import threading

CHAT_PORT = 50008

class ChatServer:
    def __init__(self, ip):
        self.ip = ip
        self.sock_chat = None
        self.thread_chat = None
        self.running = False
        self.lock = threading.Lock()

    def start_server(self):
        try:
            self.sock_chat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_chat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock_chat.bind((self.ip, CHAT_PORT))
            print(f"Сервер чата запущен на {self.ip}:{CHAT_PORT}")

            self.running = True
            self.thread_chat = threading.Thread(target=self.listen_chat, daemon=True)
            self.thread_chat.start()
        except OSError as e:
            print(f"Ошибка при запуске сервера чата: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при запуске сервера чата: {e}")

    def listen_chat(self):
        while self.running:
            try:
                # settimeout вне lock, чтобы избежать повторной установки
                self.sock_chat.settimeout(1.0)
                try:
                    msg, addr = self.sock_chat.recvfrom(1024)
                    decoded = msg.decode("utf-8")
                    print(f"Получено сообщение от {addr}: {decoded}")
                    self.handle_message(decoded)
                except socket.timeout:
                    continue  # просто таймаут — ждём дальше
                except OSError as e:
                    if self.running:
                        print(f"[recvfrom] OSError: {e}")
                    break
            except Exception as e:
                print(f"[listen_chat] Unexpected error: {e}")
                break

    def handle_message(self, msg):
        print(f"Обрабатываем сообщение: {msg}")

    def send_message(self, msg, client_ip):
        try:
            with self.lock:
                if self.sock_chat:
                    self.sock_chat.sendto(msg.encode("utf-8"), (client_ip, CHAT_PORT))
                    print(f"Отправлено сообщение: {msg} на {client_ip}:{CHAT_PORT}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")

    def stop_server(self):
        with self.lock:
            self.running = False
            if self.sock_chat:
                self.sock_chat.close()
                self.sock_chat = None
        print("Сервер чата остановлен")
