import pyaudio


def test_microphone():
    p = pyaudio.PyAudio()

    # Настройки микрофона
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024)

    print("🎤 Начало записи...")

    try:
        while True:
            data = stream.read(1024)
            print("🔊 Записываю звук...")  # Просто для проверки
    except KeyboardInterrupt:
        print("🛑 Остановка записи")
        stream.stop_stream()
        stream.close()
        p.terminate()


test_microphone()
