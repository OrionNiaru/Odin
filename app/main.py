import sys
from PyQt5.QtWidgets import QApplication
from app.ui import App  # Путь до твоего UI-класса
from app.server import ChatServer

if __name__ == "__main__":
    server = ChatServer("0.0.0.0")
    server.start_server()
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
