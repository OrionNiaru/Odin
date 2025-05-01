import socket
import struct
import threading
import cv2
import numpy as np
import mss
import tkinter as tk
from tkinter import ttk

# Параметры по умолчанию
SERVER_IP_DEFAULT = "127.0.0.1"
PORT = 60000
FRAME_WIDTH = 480
FRAME_HEIGHT = 270
JPEG_QUALITY = 40
MAX_IMAGE_DGRAM = 10
# Глобальные объекты для потоков и управления
send_thread = None
recv_thread = None
stop_event_send = None
stop_event_recv = None

def start_streaming(server_ip):
    """Запуск потока захвата экрана и отправки на сервер."""
    global send_thread, stop_event_send
    if send_thread and send_thread.is_alive():
        print("[CLIENT] Поток отправки уже запущен.")
        return
    stop_event_send = threading.Event()
    # Создаем и запускаем поток
    send_thread = threading.Thread(target=send_screen, args=(server_ip, stop_event_send))
    send_thread.daemon = True
    send_thread.start()
    print("[CLIENT] Поток отправки запущен.")

def stop_streaming():
    """Остановка потока отправки экрана."""
    global stop_event_send, send_thread
    if stop_event_send:
        stop_event_send.set()  # сигнал потокy остановиться
    if send_thread:
        send_thread.join(timeout=1.0)
    send_thread = None
    stop_event_send = None
    print("[CLIENT] Поток отправки остановлен.")

def start_receiving(server_ip):
    """Запуск потока приёма видео от сервера и отображения."""
    global recv_thread, stop_event_recv
    if recv_thread and recv_thread.is_alive():
        print("[CLIENT] Поток приёма уже запущен.")
        return
    stop_event_recv = threading.Event()
    recv_thread = threading.Thread(target=receive_screen, args=(server_ip, stop_event_recv))
    recv_thread.daemon = True
    recv_thread.start()
    print("[CLIENT] Поток приёма запущен.")

def stop_receiving():
    """Остановка потока приёма видео."""
    global stop_event_recv, recv_thread
    if stop_event_recv:
        stop_event_recv.set()  # сигнал потоку завершиться
    if recv_thread:
        recv_thread.join(timeout=2.0)  # ждем чуть дольше, т.к. может быть блокирован recv
    recv_thread = None
    stop_event_recv = None
    print("[CLIENT] Поток приёма остановлен.")

def send_screen(server_ip, stop_event):
    """Функция-поток: захват экрана и отправка кадров по UDP на сервер."""
    # Создаем UDP-сокет для отправки
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = (server_ip, PORT)
    frame_count = 0
    try:
        # Настройка mss для захвата экрана
        with mss.mss() as sct:
            # Область захвата - весь экран (потом уменьшим до FRAME_WIDTHxFRAME_HEIGHT)
            monitor = sct.monitors[1]  # [1] - первый монитор (monitors[0] - все экраны)
            print("[CLIENT] Начата трансляция экрана...")

            while not stop_event.is_set():
                frame_count += 1
                # Захват экрана
                sct_img = sct.grab(monitor)
                img = np.array(sct_img)  # Преобразуем в numpy-массив
                frame = img[:, :, :3]    # отбрасываем альфа-канал (BGRA -> BGR)
                # Масштабируем до нужного размера
                frame_resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                # Сжимаем кадр в JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                result, encimg = cv2.imencode('.jpg', frame_resized, encode_param)
                if not result:
                    print("[CLIENT] Ошибка: не удалось кодировать кадр!")
                    continue
                frame_data: bytes = encimg.tobytes()

                # Если кадр слишком большой для одного UDP-пакета, разбиваем на сегменты
                size = len(frame_data)
                # вычисляем кол-во сегментов (ceil)
                num_segments = (size + MAX_IMAGE_DGRAM - 1) // MAX_IMAGE_DGRAM
                # Отправляем фрагменты кадра
                pos = 0
                segment_no = num_segments
                # Логируем информацию о кадре
                print(f"[CLIENT] Отправка кадра {frame_count}: размер {size} байт, фрагментов {num_segments}")
                while segment_no > 0:
                    # Конец фрагмента (не включая, срез)
                    end = min(size, pos + MAX_IMAGE_DGRAM)
                    # Данные фрагмента с флагом сегмента (segment_no)
                    segment = struct.pack("B", segment_no) + frame_data[pos:end]
                    # Отправляем фрагмент серверу
                    try:
                        sock.sendto(segment, server_addr)
                    except Exception as e:
                        print(f"[CLIENT] Ошибка отправки фрагмента: {e}")
                        break
                    # Логирование отправки фрагмента (кратко)
                    if segment_no == 1:
                        print(f"[CLIENT] -> Отправлен последний фрагмент, {end-pos} байт")
                    pos = end
                    segment_no -= 1
                # Небольшая задержка, чтобы ограничить FPS и нагрузку
                cv2.waitKey(1)  # позволяем обработку GUI OpenCV, хотя окно тут не отображается
                # Можно явно добавить задержку:
                # time.sleep(0.05)  # ~20 FPS ограничение
    finally:
        sock.close()
        print("[CLIENT] Трансляция экрана завершена, сокет закрыт.")

def receive_screen(server_ip, stop_event):
    """Функция-поток: приём UDP-пакетов с фрагментами кадра и отображение видео."""
    # Создаем UDP-сокет для приема
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Привязываем к произвольному порту (0) и отправляем регистр. сообщение на сервер
    sock.bind(("", 0))
    client_addr = sock.getsockname()  # (ip,port) клиента
    try:
        # Отправляем на сервер REGISTER с нашего текущего сокета
        server_addr = (server_ip, PORT)
        sock.sendto(b"REGISTER", server_addr)
        print(f"[CLIENT] REGISTER отправлен на сервер {server_addr} от {client_addr}")
    except Exception as e:
        print(f"[CLIENT] Не удалось отправить REGISTER: {e}")
        sock.close()
        return

    # Буфер для сборки текущего кадра
    dat_buf = b""
    print("[CLIENT] Ожидание данных трансляции...")
    # Установим таймаут для recv, чтобы можно было прерывать ожидание
    sock.settimeout(1.0)
    try:
        while not stop_event.is_set():
            try:
                segment, addr = sock.recvfrom(MAX_IMAGE_DGRAM)
            except socket.timeout:
                # Проверяем, не пришел ли сигнал остановки, каждые 1 сек
                continue
            except Exception as e:
                print(f"[CLIENT] Ошибка при получении данных: {e}")
                break

            if not segment:
                continue  # пустые данные, пропускаем
            # Если пришел пакет REGISTER/UNREGISTER от сервера (в данном контексте не ожидается),
            # можно его обработать при необходимости. Здесь предполагаем, что сервер шлет только видео.
            if segment == b"REGISTER" or segment == b"UNREGISTER":
                # Не должно происходить, просто логируем
                print(f"[CLIENT] Получено служебное сообщение {segment} от сервера?")
                continue

            # Расшифровываем первый байт как сегмент-флаг (количество сегментов оставшихся или 1)
            seg_flag = struct.unpack("B", segment[0:1])[0]
            fragment_data = segment[1:]
            # Логируем получение фрагмента
            if seg_flag > 1:
                print(f"[CLIENT] <- получен фрагмент (есть еще части): {len(fragment_data)} байт")
                # Если флаг > 1, это не последний фрагмент – добавляем в буфер
                dat_buf += fragment_data
            else:
                # флаг == 1: последний фрагмент кадра
                print(f"[CLIENT] <- получен последний фрагмент: {len(fragment_data)} байт, сборка кадра...")
                dat_buf += fragment_data
                # Преобразуем байты в изображение
                try:
                    img_array = np.frombuffer(dat_buf, dtype=np.uint8)
                    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow("Screen Stream", frame)
                    else:
                        print("[CLIENT] Ошибка: не удалось декодировать кадр")
                except Exception as e:
                    print(f"[CLIENT] Ошибка декодирования/отображения кадра: {e}")
                # Отображаем кадр в окне. Для обновления окна вызываем cv2.waitKey(1).
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    # Опционально: выход по нажатию 'q'
                    stop_event.set()
                    break
                # Очищаем буфер для следующего кадра
                dat_buf = b""
    finally:
        # При завершении отправляем UNREGISTER
        try:
            sock.sendto(b"UNREGISTER", (server_ip, PORT))
            print(f"[CLIENT] UNREGISTER отправлен серверу {server_ip}:{PORT}")
        except Exception as e:
            print(f"[CLIENT] Не удалось отправить UNREGISTER: {e}")
        sock.close()
        # Закрываем окно OpenCV, если открыто
        cv2.destroyAllWindows()
        print("[CLIENT] Приём экрана завершён, сокет закрыт.")

# --- GUI (Tkinter) ---
root = tk.Tk()
root.title("Screen Share Client")
root.resizable(False, False)

# IP сервера
tk.Label(root, text="Server IP:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
server_ip_var = tk.StringVar(value=SERVER_IP_DEFAULT)
tk.Entry(root, textvariable=server_ip_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Флажки режимов
send_var = tk.BooleanVar(value=False)
recv_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Транслировать экран", variable=send_var).grid(row=1, column=0, columnspan=2, padx=5, sticky="w")
tk.Checkbutton(root, text="Принимать экран", variable=recv_var).grid(row=2, column=0, columnspan=2, padx=5, sticky="w")

# Функции для кнопок
def on_start():
    server_ip = server_ip_var.get().strip()
    if not server_ip:
        print("[CLIENT] Не указан IP сервера!")
        return
    # Запуск выбранных режимов
    if send_var.get():
        start_streaming(server_ip)
    if recv_var.get():
        start_receiving(server_ip)

def on_stop():
    # Остановка потоков (если активны)
    if send_var.get():
        stop_streaming()
    if recv_var.get():
        stop_receiving()

# Кнопки Start/Stop
btn_start = ttk.Button(root, text="Start", command=on_start)
btn_start.grid(row=3, column=0, padx=5, pady=10, sticky="e")
btn_stop = ttk.Button(root, text="Stop", command=on_stop)
btn_stop.grid(row=3, column=1, padx=5, pady=10, sticky="w")

# Обработчик закрытия окна
def on_close():
    # Останавливаем потоки при закрытии окна, чтобы корректно выйти
    try:
        stop_streaming()
    except:
        pass
    try:
        stop_receiving()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
