import socket
import threading
import pyaudio

SERVER_IP = "127.0.0.1"  # Заменить на IP сервера, если клиент на другом ПК
PORT = 50007

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

audio = pyaudio.PyAudio()

# Запись и отправка звука
def send_voice():
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("📤 Отправка звука...")
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        sock.sendto(data, (SERVER_IP, PORT))

threading.Thread(target=send_voice, daemon=True).start()
input("🎧 Голосовой клиент запущен. Нажми Enter для выхода...\n")
