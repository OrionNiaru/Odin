import socket
import threading
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
PORT = 50007

audio = pyaudio.PyAudio()

# Поток для воспроизведения
def receive_voice():
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    print("🟢 Ожидание звука...")
    while True:
        data, _ = sock.recvfrom(2048)
        stream.write(data)

threading.Thread(target=receive_voice, daemon=True).start()
input("🎤 Сервер готов. Запусти client.py на другом компьютере и нажми Enter для выхода...\n")