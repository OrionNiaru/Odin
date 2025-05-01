import socket
import threading

VOICE_PORT = 50007
CHAT_PORT = 50008
VIDEO_PORT = 60000

voice_clients = set()
chat_clients = set()
video_clients = set()

def handle_voice():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", VOICE_PORT))
    print(f"🎙 Голосовой сервер на порту {VOICE_PORT}")
    while True:
        data, addr = sock.recvfrom(2048)
        if addr not in voice_clients:
            voice_clients.add(addr)
            print(f"🔊 Новый голосовой клиент: {addr}")
        for client in voice_clients:
            if client != addr:
                sock.sendto(data, client)

def handle_chat():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", CHAT_PORT))
    print(f"💬 Чат-сервер на порту {CHAT_PORT}")
    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"REGISTER":
            if addr not in chat_clients:
                chat_clients.add(addr)
                print(f"🟢 Зарегистрирован чат-клиент: {addr}")
            continue
        elif data == b"UNREGISTER":
            if addr in chat_clients:
                chat_clients.remove(addr)
                print(f"🔴 Вышел из чата: {addr}")
            continue
        print(f"📨 {addr} → {data.decode(errors='ignore')}")
        for client in chat_clients:
            if client != addr:
                sock.sendto(data, client)

def handle_video():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", VIDEO_PORT))
    print(f"📺 Видео-сервер на порту {VIDEO_PORT}")
    while True:
        data, addr = sock.recvfrom(1024)
        if addr not in video_clients:
            video_clients.add(addr)
            print(f"🖥️ Новый видеоклиент: {addr}")
        for client in video_clients:
            if client != addr:
                sock.sendto(data, client)

threading.Thread(target=handle_voice, daemon=True).start()
threading.Thread(target=handle_chat, daemon=True).start()
threading.Thread(target=handle_video, daemon=True).start()

input("🟢 Сервер запущен. Нажми Enter для выхода...")