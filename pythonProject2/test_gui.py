import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout


class MyGUIApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = QWidget()
        self.init_gui()

    def init_gui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Hello, PyQt!")
        layout.addWidget(self.label)

        self.button = QPushButton("Click me!")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)

        self.main_window.setLayout(layout)
        self.main_window.setWindowTitle("PyQt Example")
        self.main_window.setGeometry(100, 100, 300, 200)

    def on_button_click(self):
        self.label.setText("Button Clicked!")

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    gui_app = MyGUIApp()
    gui_app.run()
