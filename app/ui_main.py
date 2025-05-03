from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QCheckBox
)
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtCore import Qt
from app.threads.video_thread import VideoThread
from app.threads.audio_thread import AudioThread
from app.threads.audio_reciever_thread import AudioReceiverThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🐾 Кото-Чат UwU")
        self.setGeometry(100, 100, 1000, 600)
        self.video_thread = None
        self.audio_thread = None
        self.audio_receiver_thread = None
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # IP и Порт
        top_layout = QHBoxLayout()
        self.ip_entry = QLineEdit()
        self.ip_entry.setPlaceholderText("IP сервера")
        self.port_entry = QLineEdit()
        self.port_entry.setPlaceholderText("Порт")
        self.start_btn = QPushButton("Запуск")
        self.start_btn.clicked.connect(self.start_clicked)
        top_layout.addWidget(self.ip_entry)
        top_layout.addWidget(self.port_entry)
        top_layout.addWidget(self.start_btn)

        # Ник
        self.nickname_entry = QLineEdit()
        self.nickname_entry.setPlaceholderText("Введите ник")

        # Чат
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Courier", 10))

        # Логи
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Courier", 10))

        # Чекбоксы
        self.checkbox_audio = QCheckBox("📢 Звук")
        self.checkbox_video = QCheckBox("🎥 Видео (Вебкамера)")
        self.checkbox_watch_screen = QCheckBox("🖥 Смотреть экран")
        self.checkbox_debug = QCheckBox("🐞 Debug")

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.checkbox_audio)
        checkbox_layout.addWidget(self.checkbox_video)
        checkbox_layout.addWidget(self.checkbox_watch_screen)
        checkbox_layout.addWidget(self.checkbox_debug)

        # Видео
        self.video_label = QLabel("📺 Видео")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #ddd; min-height: 300px;")

        # Сообщение
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Напишите сообщение...")
        self.send_btn = QPushButton("Отправить")
        self.send_btn.clicked.connect(self.send_message)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.message_input)
        bottom_layout.addWidget(self.send_btn)

        # Сборка
        layout.addLayout(top_layout)
        layout.addWidget(self.nickname_entry)
        layout.addWidget(self.chat_area)
        layout.addLayout(checkbox_layout)
        layout.addWidget(self.video_label)
        layout.addWidget(self.log_area)
        layout.addLayout(bottom_layout)
        main_widget.setLayout(layout)

        # Чекбоксы
        self.checkbox_video.toggled.connect(self.toggle_video)
        self.checkbox_watch_screen.toggled.connect(self.toggle_screen)

    def start_clicked(self):
        nickname = self.nickname_entry.text()
        if not nickname:
            self.log_area.append("❌ Введите ник для подключения.")
            return

        ip = self.ip_entry.text()
        try:
            port = int(self.port_entry.text())
        except ValueError:
            self.log_area.append("❌ Некорректный порт.")
            return

        self.log_area.append(f"🚀 Старт: {nickname} ({ip}:{port})")

        if self.checkbox_audio.isChecked():
            self.start_audio_thread(ip, port)
            self.log_area.append("🎧 Аудио поток запущен")

        watch_screen = self.checkbox_watch_screen.isChecked()
        video = self.checkbox_video.isChecked()

        if video and watch_screen:
            self.log_area.append("❌ Выберите только одно видео: экран или вебкамера.")
            return

        if video or watch_screen:
            self.video_thread = VideoThread(watch_screen=watch_screen, use_webcam=video)
            self.video_thread.frame_received.connect(self.update_video_frame)
            self.video_thread.start()
            self.log_area.append("🎥 Видео поток запущен")

    def toggle_video(self, checked):
        if checked:
            self.start_video()
        else:
            self.stop_video()

    def toggle_screen(self, checked):
        if checked:
            self.start_screen()
        else:
            self.stop_screen()

    def start_audio_thread(self, ip, port):
        self.audio_thread = AudioThread(server_ip=ip, server_port=port)
        self.audio_thread.start()

        self.audio_receiver_thread = AudioReceiverThread(server_ip=ip, server_port=port)
        self.audio_receiver_thread.start()

    def stop_audio_thread(self):
        if self.audio_thread:
            self.audio_thread.stop()  # Если у вас есть механизм для остановки потока
            self.audio_thread.close_socket()  # Закрыть сокет вручную
            self.audio_thread = None

        if self.audio_receiver_thread:
            self.audio_receiver_thread.stop()  # Остановка потока
            self.audio_receiver_thread.close_socket()  # Закрыть сокет вручную
            self.audio_receiver_thread = None

    def start_video(self):
        self.log_area.append("🎥 Включение вебкамеры...")
        if not self.video_thread or not self.video_thread.is_alive():
            self.video_thread = VideoThread(watch_screen=False, use_webcam=True)
            self.video_thread.frame_received.connect(self.update_video_frame)
            self.video_thread.start()

    def stop_video(self):
        self.log_area.append("🎥 Выключение вебкамеры...")
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.stop()
            self.video_thread = None

    def start_screen(self):
        self.log_area.append("🖥 Включение демонстрации экрана...")
        if not self.video_thread or not self.video_thread.is_alive():
            self.video_thread = VideoThread(watch_screen=True, use_webcam=False)
            self.video_thread.frame_received.connect(self.update_video_frame)
            self.video_thread.start()

    def stop_screen(self):
        self.log_area.append("🖥 Выключение демонстрации экрана...")
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.stop()
            self.video_thread = None

    def update_video_frame(self, image: QImage):
        self.video_label.setPixmap(QPixmap.fromImage(image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def send_message(self):
        message = self.message_input.text()
        if message:
            nickname = self.nickname_entry.text()
            if not nickname:
                self.chat_area.append("❌ Введите ник.")
                return
            self.chat_area.append(f"{nickname}: {message}")
            self.message_input.clear()
            # Здесь может быть: self.client.send_message(message)

    def closeEvent(self, event):
        # Закрываем все потоки перед закрытием окна
        if self.video_thread:
            self.video_thread.stop()
        if self.audio_thread:
            self.audio_thread.stop()
        if self.audio_receiver_thread:
            self.audio_receiver_thread.stop()
        event.accept()
