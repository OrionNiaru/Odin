# server.py — ретранслятор
import socket
import threading

PORT = 50007
clients = set()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))

def server_loop():
    print("🟢 Сервер запущен...")
    while True:
        data, addr = sock.recvfrom(2048)
        if addr not in clients:
            clients.add(addr)
            print(f"➕ Новый клиент: {addr}")
        for client in clients:
            if client != addr:
                sock.sendto(data, client)

threading.Thread(target=server_loop, daemon=True).start()
input("🎤 Сервер работает. Нажми Enter для выхода...\n")
