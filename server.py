import socket
import struct

# Настройки
PORT = 60000  # порт для приема/передачи UDP
MAX_DGRAM = 2**16  # максимальный размер датаграммы UDP
# Чтобы избежать переполнения, полезная нагрузка ограничивается чуть меньше 65535&#8203;:contentReference[oaicite:3]{index=3}:
MAX_IMAGE_DGRAM = MAX_DGRAM - 64  # ~65472 байт максимальный размер фрагмента изображения

# Создаем UDP-сокет и привязываем к порту
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
print(f"Server started, listening on port {PORT}")

clients = []  # список адресов клиентов-получателей

while True:
    try:
        data, addr = sock.recvfrom(MAX_DGRAM)
    except KeyboardInterrupt:
        print("Server stopped by user")
        break

    # Проверка на служебные сообщения регистрации
    if data == b"REGISTER":
        if addr not in clients:
            clients.append(addr)
            print(f"[SERVER] REGISTER: клиент {addr} добавлен в список рассылки")
        # отправлять подтверждение не требуется
        continue
    elif data == b"UNREGISTER":
        if addr in clients:
            clients.remove(addr)
            print(f"[SERVER] UNREGISTER: клиент {addr} удалён из списка рассылки")
        continue

    # Если это не служебное сообщение, считаем пакетом фрагмента кадра
    # Логируем получение фрагмента (первые байты включают номер сегмента)
    if len(data) > 0:
        seg_flag = data[0]  # первый байт: флаг сегмента (количество оставшихся сегментов или 1 для последнего)
    else:
        seg_flag = None
    print(f"[SERVER] Получен фрагмент от {addr}: размер {len(data)} байт, seg_flag={seg_flag}")

    # Пересылка фрагмента всем клиентам (кроме отправителя)
    # Если клиентов нет, пакет просто игнорируется
    for client_addr in clients:
        if client_addr == addr:
            continue  # не отправляем обратно отправителю
        try:
            sock.sendto(data, client_addr)
        except Exception as e:
            print(f"[SERVER] Ошибка отправки клиенту {client_addr}: {e}")
    if clients:
        # Логируем факт ретрансляции
        print(f"[SERVER] Фрагмент от {addr} разослан {len(clients) - (1 if addr in clients else 0)} получателям")
