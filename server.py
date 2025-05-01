import socket
import threading

VOICE_PORT = 50008  # Порт для аудио
VIDEO_PORT = 60001  # Порт для видео

voice_clients = set()
video_clients = set()

sock_voice = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock_voice.bind(("0.0.0.0", VOICE_PORT))
sock_video.bind(("0.0.0.0", VIDEO_PORT))

def relay(sock, clients, name):
    while True:
        data, addr = sock.recvfrom(2048)
        if addr not in clients:
            clients.add(addr)
            print(f"➕ Новый {name} клиент: {addr}")
        for client in clients:
            if client != addr:
                sock.sendto(data, client)

threading.Thread(target=relay, args=(sock_voice, voice_clients, "аудио"), daemon=True).start()
threading.Thread(target=relay, args=(sock_video, video_clients, "видео"), daemon=True).start()

input("🎤 Сервер работает. Нажми Enter для выхода...\n")
