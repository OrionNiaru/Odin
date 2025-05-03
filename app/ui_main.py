from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QCheckBox
)
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtCore import Qt
from app.threads.video_thread import VideoThread
from app.threads.audio_thread import AudioThread, AudioReceiverThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🐾 Кото-Чат UwU")
        self.setGeometry(100, 100, 1000, 600)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # Ввод IP и Порта
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

        # Ввод ника
        self.nickname_entry = QLineEdit()
        self.nickname_entry.setPlaceholderText("Введите ник")

        # Чат
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Courier", 10))

        # Лог Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Courier", 10))

        # Чекбоксы для аудио и видео
        self.checkbox_audio = QCheckBox("📢 Звук")
        self.checkbox_video = QCheckBox("🎥 Видео (Вебкамера)")
        self.checkbox_watch_screen = QCheckBox("🖥 Смотреть экран")
        self.checkbox_debug = QCheckBox("🐞 Debug")

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.checkbox_audio)
        checkbox_layout.addWidget(self.checkbox_video)
        checkbox_layout.addWidget(self.checkbox_watch_screen)
        checkbox_layout.addWidget(self.checkbox_debug)

        # Видео область
        self.video_label = QLabel("📺 Видео")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #ddd; min-height: 300px;")

        # Расположение элементов
        layout.addLayout(top_layout)
        layout.addWidget(self.nickname_entry)
        layout.addWidget(self.chat_area)
        layout.addLayout(checkbox_layout)
        layout.addWidget(self.video_label)
        layout.addWidget(self.log_area)

        # Поле для ввода сообщения
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Напишите сообщение...")

        # Кнопка отправки
        self.send_btn = QPushButton("Отправить")
        self.send_btn.clicked.connect(self.send_message)

        # Размещение внизу
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.message_input)
        bottom_layout.addWidget(self.send_btn)

        layout.addLayout(bottom_layout)

        # Устанавливаем layout для главного окна
        main_widget.setLayout(layout)

        self.video_thread = None

        # Подключаем обработчики событий для чекбоксов
        self.checkbox_video.toggled.connect(self.toggle_video)
        self.checkbox_watch_screen.toggled.connect(self.toggle_screen)

    def start_clicked(self):
        # Получаем никнейм
        nickname = self.nickname_entry.text()
        if not nickname:
            self.log_area.append("❌ Введите ник для подключения.")
            return

        self.log_area.append(f"🚀 Старт нажали! Ник: {nickname}")

        # Проверка на выбранные источники видео
        watch_screen = self.checkbox_watch_screen.isChecked()
        video = self.checkbox_video.isChecked()

        # Проверка на некорректный выбор
        if watch_screen and video:
            self.log_area.append("❌ Выберите только один источник видео: экран или вебкамера.")
            return

        if video or watch_screen:
            self.video_thread = VideoThread(watch_screen=watch_screen, use_webcam=video)
            self.video_thread.frame_received.connect(self.update_video_frame)
            self.video_thread.start()
            self.log_area.append("🎥 Видео запущено")

    def toggle_video(self, checked):
        """Переключение состояния видео (вебкамера)."""
        if checked:
            self.start_video()
        else:
            self.stop_video()

    def toggle_screen(self, checked):
        """Переключение состояния демонстрации экрана."""
        if checked:
            self.start_screen()
        else:
            self.stop_screen()

    def start_audio_thread(self):
        # Запуск потока для записи и передачи аудио
        self.audio_thread = AudioThread(server_ip="127.0.0.1", server_port=5000)
        self.audio_thread.start()

        # Запуск потока для получения и воспроизведения аудио
        self.audio_receiver_thread = AudioReceiverThread(server_ip="127.0.0.1", server_port=5000)
        self.audio_receiver_thread.start()

    def stop_audio_thread(self):
        self.audio_thread.stop()
        self.audio_receiver_thread.stop()

    def start_video(self):
        """Запуск видео с вебкамеры."""
        self.log_area.append("🎥 Включение вебкамеры...")
        if self.video_thread is None:
            self.video_thread = VideoThread(watch_screen=False, use_webcam=True)
            self.video_thread.frame_received.connect(self.update_video_frame)
            self.video_thread.start()

    def stop_video(self):
        """Остановка видео с вебкамеры."""
        self.log_area.append("🎥 Выключение вебкамеры...")
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread = None

    def start_screen(self):
        """Запуск демонстрации экрана."""
        self.log_area.append("🖥 Включение демонстрации экрана...")
        if self.video_thread is None:
            self.video_thread = VideoThread(watch_screen=True, use_webcam=False)
            self.video_thread.frame_received.connect(self.update_video_frame)
            self.video_thread.start()

    def stop_screen(self):
        """Остановка демонстрации экрана."""
        self.log_area.append("🖥 Выключение демонстрации экрана...")
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread = None

    def update_video_frame(self, image: QImage):
        """Обновление изображения видео/экрана."""
        self.video_label.setPixmap(QPixmap.fromImage(image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def send_message(self):
        # Получаем сообщение из поля ввода
        message = self.message_input.text()
        if message:
            nickname = self.nickname_entry.text()
            if not nickname:
                self.chat_area.append("❌ Введите ник для отправки сообщения.")
                return
            # Отправляем сообщение в чат
            self.chat_area.append(f"{nickname}: {message}")
            self.message_input.clear()
