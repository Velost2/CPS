import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from socket import *


class ClientWorker(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ClientWorker, self).__init__(parent)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(("192.168.178.124", 5007))

    def run(self):
        while True:
            try:
                data_recv = self.client_socket.recv(1024).decode()
                if data_recv:
                    self.message_received.emit(data_recv)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def send_message(self, message):
        try:
            if message:
                self.client_socket.sendall(message.encode())
                print(f"Message sent: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")


class MyClientGUI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.worker = ClientWorker()
        self.main_window = QWidget()
        self.init_gui()
        self.worker.message_received.connect(self.update_gui)
        self.worker.start()

    def init_gui(self):
        self.layout = QVBoxLayout()

        self.label_received = QLabel("Received Messages:")
        self.label_received.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.label_received)

        self.input_message = QLineEdit()
        self.input_message.setPlaceholderText("Enter your message")
        self.input_message.returnPressed.connect(self.send_message)
        self.layout.addWidget(self.input_message)

        self.send_button = QPushButton("Send Message")
        self.send_button.setFont(QFont("Arial", 14))
        self.send_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.send_button)

        self.stop_button = QPushButton("Stop Client")
        self.stop_button.setFont(QFont("Arial", 14))
        self.stop_button.clicked.connect(self.worker.quit)
        self.layout.addWidget(self.stop_button)

        self.main_window.setLayout(self.layout)
        self.main_window.setWindowTitle("Client GUI")
        self.main_window.setGeometry(100, 100, 400, 200)

    def update_gui(self, message):
        self.label_received.setText(f"Received Messages: {message}")

    def send_message(self):
        message = self.input_message.text()
        self.worker.send_message(message)
        self.input_message.clear()

    def stopp_connection(self):
        self.worker.quit()
        self.app.quit()


if __name__ == "__main__":
    client_gui = MyClientGUI()
    client_gui.main_window.show()
    sys.exit(client_gui.app.exec_())
