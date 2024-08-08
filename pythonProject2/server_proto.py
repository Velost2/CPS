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
from PyQt5.QtCore import QTimer
from socket import *


class MyServerGUI:
    def __init__(self):
        self.data_received = None
        self.data_sent = None
        self.app = QApplication(sys.argv)
        self.main_window = QWidget()
        self.init_gui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(1000)

    def init_gui(self):
        self.layout = QVBoxLayout()

        self.label_received = QLabel("Received Messages:")
        self.label_received.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.label_received)

        self.label_sent = QLabel("Sent Messages:")
        self.label_sent.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.label_sent)

        self.input_message = QLineEdit()  # Hier fügen wir ein Eingabefeld hinzu
        self.input_message.setPlaceholderText("Enter your message")  # Platzhaltertext
        self.layout.addWidget(self.input_message)

        self.send_button = QPushButton("Send Message")
        self.send_button.setFont(QFont("Arial", 14))
        self.send_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.send_button)

        self.stop_button = QPushButton("Stop Server")
        self.stop_button.setFont(QFont("Arial", 14))
        self.stop_button.clicked.connect(self.stopp_connection)
        self.layout.addWidget(self.stop_button)

        self.main_window.setLayout(self.layout)
        self.main_window.setWindowTitle("Server GUI")
        self.main_window.setGeometry(
            100, 100, 400, 300
        )  # Ändere die Größe des Fensters

    def update_gui(self):
        try:
            with socket(AF_INET, SOCK_STREAM) as client_socket:
                client_socket.connect(("localhost", 5007))
                data_recv = client_socket.recv(1024).decode()
                if data_recv:
                    self.label_received.setText(f"Received Messages: {data_recv}")

                data_sent = "server " + str("hallo") + " Noch: " + str(30) + " Sekunden"
                self.label_sent.setText(f"Sent Messages: {data_sent}")
        except Exception as e:
            print(f"Error updating GUI: {e}")

    def send_message(self):
        try:
            with socket(AF_INET, SOCK_STREAM) as client_socket:
                client_socket.connect(("localhost", 5007))
                message = self.input_message.text()
                if message:
                    client_socket.send(message.encode())
                    print(f"Message sent: {message}")
                    self.input_message.clear()  # Leere das Eingabefeld
        except Exception as e:
            print(f"Error sending message: {e}")

    def stopp_connection(self):
        self.app.quit()


if __name__ == "__main__":
    gui = MyServerGUI()
    gui.main_window.show()
    sys.exit(gui.app.exec_())
