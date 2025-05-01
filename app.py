import tkinter as tk
from tkinter import messagebox
import queue
import cv2
from multi_client_gui import VoiceScreenClient

class App:
    def __init__(self, root):
        self.root = root
        self.client = None
        self.client_running = False
        self.frame_queue = queue.Queue()
        self.build_gui()
        self.root.after(33, self.update_frame)

    def build_gui(self):
        self.root.title("Голос и экран клиент")
        self.root.geometry("300x250")

        tk.Label(self.root, text="IP сервера:").pack(pady=5)
        self.ip_entry = tk.Entry(self.root)
        self.ip_entry.pack()
        self.ip_entry.insert(0, "127.0.0.1")

        self.voice_var = tk.BooleanVar(value=True)
        self.screen_send_var = tk.BooleanVar()
        self.screen_recv_var = tk.BooleanVar()

        tk.Checkbutton(self.root, text="Транслировать экран", variable=self.screen_send_var).pack()
        tk.Checkbutton(self.root, text="Смотреть экран", variable=self.screen_recv_var).pack()

        self.start_btn = tk.Button(self.root, text="Запустить", command=self.start_client)
        self.start_btn.pack(pady=10)

        self.stop_btn = tk.Button(self.root, text="Остановить", command=self.stop_client, state=tk.DISABLED)
        self.stop_btn.pack()

    def start_client(self):
        if self.client_running:
            messagebox.showinfo("Уже работает", "Клиент уже запущен")
            return

        ip = self.ip_entry.get()
        if not ip:
            messagebox.showerror("Ошибка", "Введите IP сервера")
            return

        self.client = VoiceScreenClient(ip, frame_queue=self.frame_queue)
        self.client.start(
            stream_screen=self.screen_send_var.get(),
            watch_screen=self.screen_recv_var.get()
        )
        self.client_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_client(self):
        if self.client:
            self.client.stop()
        self.client_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def update_frame(self):
        if not self.frame_queue.empty():
            frame = self.frame_queue.get()
            if frame is not None:
                cv2.imshow("📺 Экран", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    self.stop_client()
                    cv2.destroyAllWindows()
        self.root.after(30, self.update_frame)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
