import socket
import threading

PORT = 50007
clients = {}
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))

print(f"🟢 Сервер запущен на порту {PORT}")

def relay():
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            if addr not in clients:
                clients[addr] = {"nickname": f"{addr[0]}:{addr[1]}"}
                print(f"➕ Новый клиент: {clients[addr]['nickname']}")

            for client_addr in clients:
                if client_addr != addr:
                    sock.sendto(data, client_addr)
        except Exception as e:
            print(f"❌ Ошибка: {e}")

threading.Thread(target=relay, daemon=True).start()

try:
    while True:
        cmd = input("🔧 Введите 'list' для списка клиентов или 'exit' для выхода: ").strip()
        if cmd == 'list':
            print("👥 Подключённые клиенты:")
            for i, (addr, info) in enumerate(clients.items(), 1):
                print(f" {i}. {info['nickname']} @ {addr}")
        elif cmd == 'exit':
            print("🛑 Сервер остановлен")
            break
except KeyboardInterrupt:
    print("\n🛑 Сервер завершён вручную")
