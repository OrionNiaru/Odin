import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from app.client import VoiceClient
from app.settings import load_settings, save_settings

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.client = None
        self.setWindowTitle("🐾 Кото-Чат UwU")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("background-color: #fff0f5;")
        self.build_gui()
        self.load_settings()

    def build_gui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.ip_entry = QLineEdit(self)
        self.ip_entry.setPlaceholderText("IP сервера")
        self.name_entry = QLineEdit(self)
        self.name_entry.setPlaceholderText("Никнейм")

        self.stream_var = QCheckBox("Транслировать экран", self)
        self.watch_var = QCheckBox("Смотреть экран", self)

        self.status_label = QLabel("🔴 Отключён", self)

        self.start_btn = QPushButton("Запуск", self)
        self.start_btn.clicked.connect(self.start_client)

        self.stop_btn = QPushButton("Стоп", self)
        self.stop_btn.clicked.connect(self.stop_client)
        self.stop_btn.setDisabled(True)

        self.mute_btn = QPushButton("Mute (F1)", self)
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.mute_btn.setDisabled(True)

        self.chat_box = QTextEdit(self)
        self.chat_box.setDisabled(True)
        self.chat_entry = QLineEdit(self)
        self.send_btn = QPushButton("Отправить", self)
        self.send_btn.clicked.connect(self.send_chat)

        self.video_label = QLabel(self)
        self.video_label.setPixmap(QPixmap())  # Заглушка

        # Размещение элементов
        left_layout.addWidget(QLabel("IP сервера:"))
        left_layout.addWidget(self.ip_entry)
        left_layout.addWidget(QLabel("Никнейм:"))
        left_layout.addWidget(self.name_entry)
        left_layout.addWidget(self.stream_var)
        left_layout.addWidget(self.watch_var)
        left_layout.addWidget(self.status_label)

        left_layout.addWidget(self.start_btn)
        left_layout.addWidget(self.stop_btn)
        left_layout.addWidget(self.mute_btn)

        left_layout.addWidget(QLabel("Общий чат 🐾"))
        left_layout.addWidget(self.chat_box)
        left_layout.addWidget(self.chat_entry)
        left_layout.addWidget(self.send_btn)

        right_layout.addWidget(self.video_label)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        self.setLayout(main_layout)

    def start_client(self):
        ip = self.ip_entry.text().strip()
        name = self.name_entry.text().strip() or "Котик"
        self.client = VoiceClient(ip, name, self.chat_log, self.update_video,
                                  stream_screen=self.stream_var.isChecked(), watch_screen=self.watch_var.isChecked())
        self.client.start()
        self.status_label.setText(f"🟢 Подключён как {name}")
        self.start_btn.setDisabled(True)
        self.stop_btn.setEnabled(True)
        self.mute_btn.setEnabled(True)
        self.save_settings()

    def stop_client(self):
        if self.client:
            self.client.stop()
        self.client = None
        self.status_label.setText("🔴 Отключён")
        self.start_btn.setEnabled(True)
        self.stop_btn.setDisabled(True)
        self.mute_btn.setDisabled(True)

    def toggle_mute(self):
        if self.client:
            muted = self.client.toggle_mute()
            self.mute_btn.setText("Unmute (F1)" if muted else "Mute (F1)")
            self.chat_log("🔇 Микрофон выключен\n" if muted else "🎤 Микрофон включен\n")

    def send_chat(self):
        msg = self.chat_entry.text().strip()
        if msg and self.client:
            self.client.send_chat_message(msg)
            self.chat_log(f"[🐾 {self.client.nickname}]: {msg}\n")
            self.chat_entry.clear()

    def chat_log(self, message):
        self.chat_box.append(message)

    def update_video(self, img):
        self.video_label.setPixmap(img)

    def load_settings(self):
        settings = load_settings()
        self.ip_entry.setText(settings.get("ip", ""))
        self.name_entry.setText(settings.get("nickname", ""))

    def save_settings(self):
        settings = {
            "ip": self.ip_entry.text().strip(),
            "nickname": self.name_entry.text().strip()
        }
        save_settings(settings)
