import socket
import threading

HOST = '0.0.0.0'
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []

# --- Рассылка сообщений всем ---
def broadcast(data, sender):
    for client in clients:
        if client != sender:
            try:
                client.sendall(data)
            except:
                clients.remove(client)

# --- Обработка клиента ---
def handle_client(conn, addr):
    print(f"✅ Подключение от {addr}")
    clients.append(conn)
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            broadcast(data, conn)
        except:
            break
    print(f"❌ {addr} отключился")
    clients.remove(conn)
    conn.close()

# --- Основной цикл сервера ---
print(f"🚀 Сервер запущен на {HOST}:{PORT}")
while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
    thread.start()
