import socket
import threading

VOICE_PORT = 50007
CHAT_PORT = 50008

voice_clients = set()
chat_clients = set()

def handle_voice():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", VOICE_PORT))
    print(f"🎙 Сервер голосового чата запущен на порту {VOICE_PORT}")
    while True:
        data, addr = sock.recvfrom(2048)
        if addr not in voice_clients:
            voice_clients.add(addr)
            print(f"➕ Новый голосовой клиент: {addr}")
        for client in voice_clients:
            if client != addr:
                sock.sendto(data, client)

def handle_chat():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", CHAT_PORT))
    print(f"💬 Сервер чата запущен на порту {CHAT_PORT}")
    while True:
        data, addr = sock.recvfrom(1024)

        if data == b"REGISTER":
            if addr not in chat_clients:
                chat_clients.add(addr)
                print(f"🟢 Зарегистрирован чат-клиент {addr}")
            continue
        elif data == b"UNREGISTER":
            if addr in chat_clients:
                chat_clients.remove(addr)
                print(f"🔴 Клиент вышел из чата: {addr}")
            continue

        print(f"💬 Получено сообщение от {addr}: {data.decode('utf-8')}")

        # Рассылка всем, кроме отправителя
        for client in chat_clients:
            if client != addr:
                sock.sendto(data, client)

threading.Thread(target=handle_voice, daemon=True).start()
threading.Thread(target=handle_chat, daemon=True).start()
input("🟢 Сервер запущен. Нажмите Enter для выхода...\n")
