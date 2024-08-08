import sys
import threading
import time
import Adafruit_ADS1x15
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QScrollArea
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from socket import *
from PyQt5.QtCore import QObject, pyqtSignal
from picamera import PiCamera

adc_channel_0 = 0

class MyTemp(QObject):
    new_temperature = pyqtSignal(float)  # Signal, das die neue Temperatur sendet

    def __init__(self, gain, sps):
        super().__init__()
        self.adc = Adafruit_ADS1x15.ADS1115()
        self.raw_data = None
        self.voltage_mess = None
        self.temperatur = None
        self.gain = gain
        self.samples_per_seconds = sps
        self.xs = []
        self.ys = []

    def meas_temperature(self, channel):
        self.raw_data = self.adc.read_adc(channel, self.gain, self.samples_per_seconds)
        self.voltage_mess = float(self.raw_data) / 32767.0 * 4.095
        temp = np.log((10000 / self.voltage_mess) * (3.3 - self.voltage_mess))
        temp = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * np.power(temp, 2))) * temp)
        self.temperatur = temp - 273.13
        self.new_temperature.emit(self.temperatur)

    def update_new_data(self):
        if self.xs == []:
            self.xs.append(1)
        else:
            self.xs.append(self.xs[-1] + 1)
        self.ys.append(self.temperatur)

    def measure_and_update(self):
        self.meas_temperature(adc_channel_0)
        self.update_new_data()

class MyTask():
    def __init__(self, timer_periode, hFunction, duration):
        self.timer_periode = timer_periode
        self.hFunction = hFunction
        self.duration = duration
        self.elapsed_time = 0
        self.thread = threading.Timer(self.timer_periode, self.handle_function)

    def handle_function(self):
        self.elapsed_time += self.timer_periode
        self.hFunction()

        if self.elapsed_time < self.duration:
            self.thread = threading.Timer(self.timer_periode, self.handle_function)
            self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()


class ClientWorker(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ClientWorker, self).__init__(parent)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(("192.168.178.143", 5068))

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



class MyClient:
    def __init__(self, temp_instance):
        self.server_port = 5068
        self.bufsize = 1024
        self.host = "192.168.178.143"
        self.temp_instance = temp_instance
        self.socket_connection = socket(AF_INET, SOCK_STREAM)
        self.socket_connection.connect((self.host, self.server_port))
        print("Verbunden mit dem server: %s" % (self.host))
        self.high_temp_limit = 30  # Standardwerte
        self.medium_temp_limit = 25
        self.low_temp_limit = 20
        self.thread_send = threading.Thread(target=self.worker_send)
        self.thread_send.start()

    def worker_send(self):
        previous_temperature_category = None
        while True:
            self.temp_instance.measure_and_update()
            temp = self.temp_instance.temperatur
            if temp is not None:
                if temp >= self.high_temp_limit:
                    current_temperature_category = "300"
                elif temp >= self.medium_temp_limit:
                    current_temperature_category = "250"
                elif temp >= self.low_temp_limit:
                    current_temperature_category = "200"
                else:
                    current_temperature_category = "normal"

                if current_temperature_category != previous_temperature_category:
                    self.socket_connection.send(current_temperature_category.encode())
                    previous_temperature_category = current_temperature_category
            time.sleep(5)

    def set_temperature_limits(self, high, medium, low):
        self.high_temp_limit = high
        self.medium_temp_limit = medium
        self.low_temp_limit = low

class OvenWatcher(QObject):
    fire_status_signal = pyqtSignal(str)  # Signal, um den Ofenstatus zu senden

    def __init__(self):
        super().__init__()
        self.camera = PiCamera()
        self.camera.resolution = (128, 112)
        self.check_interval = 5  # Standardintervall in Sekunden

    def is_fire_low(self, image):
        # Implementieren Sie die Logik zur Erkennung eines niedrigen Feuers
        region_of_interest = image[40:80, 44:84]  # Beispielbereich
        return np.mean(region_of_interest) < 80  # Schwellenwert für niedriges Feuer

    def check_fire(self):
        while True:
            output = np.empty((112, 128, 3), dtype=np.uint8)
            self.camera.capture(output, 'rgb')
            if self.is_fire_low(output):
                self.fire_status_signal.emit("Achtung: Das Feuer im Ofen ist niedrig!")
            else:
                self.fire_status_signal.emit("Der Ofen brennt normal.")
            time.sleep(self.check_interval)

    def set_check_interval(self, interval):
        self.check_interval = interval

class MyClientGUI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.temp_sense = MyTemp(1, 64)  # Verwenden Sie die geänderte MyTemp-Klasse
        self.client = MyClient(self.temp_sense)
        self.main_window = QWidget()
        self.scroll_area = QScrollArea()  # Scrollbar hinzufügen
        self.scroll_widget = QWidget()
        self.layout = QVBoxLayout(self.scroll_widget)  # Layout im scroll_widget
        self.init_gui()
        self.init_labels()
        self.temp_sense.new_temperature.connect(self.update_temperature_label)
        self.oven_watcher = OvenWatcher()
        self.oven_watcher_thread = QThread()
        self.oven_watcher.moveToThread(self.oven_watcher_thread)
        self.oven_watcher_thread.started.connect(self.oven_watcher.check_fire)
        self.oven_watcher.fire_status_signal.connect(self.update_fire_status_label)
        self.oven_watcher_thread.start()

        self.scroll_area.setWidget(self.scroll_widget)  # Scrollbar-Widget setzen
        self.scroll_area.setWidgetResizable(True)
        main_layout = QVBoxLayout(self.main_window)  # Hauptlayout des Fensters
        main_layout.addWidget(self.scroll_area)

        self.main_window.setWindowTitle("Client GUI")
        self.main_window.setGeometry(100, 100, 400, 400)

    def init_labels(self):
        self.label_high_limit = QLabel(f"Höchste Temperatur (aktualisiert): {self.client.high_temp_limit}")
        self.label_medium_limit = QLabel(f"Mittlere Temperatur (aktualisiert): {self.client.medium_temp_limit}")
        self.label_low_limit = QLabel(f"Niedrige Temperatur (aktualisiert): {self.client.low_temp_limit}")
        self.layout.addWidget(self.label_high_limit)
        self.layout.addWidget(self.label_medium_limit)
        self.layout.addWidget(self.label_low_limit)

    def init_gui(self):
        self.label_temperature = QLabel("Aktuelle Temperatur: ")
        self.label_temperature.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.label_temperature)

        self.temp_limit_high = QLineEdit()
        self.temp_limit_medium = QLineEdit()
        self.temp_limit_low = QLineEdit()
        self.update_temp_limits_button = QPushButton("Temperaturen aktualisieren")
        self.update_temp_limits_button.clicked.connect(self.update_temperature_limits)

        self.layout.addWidget(QLabel("Höchste Temperatur:"))
        self.layout.addWidget(self.temp_limit_high)
        self.layout.addWidget(QLabel("Mittlere Temperatur:"))
        self.layout.addWidget(self.temp_limit_medium)
        self.layout.addWidget(QLabel("Niedrige Temperatur:"))
        self.layout.addWidget(self.temp_limit_low)
        self.layout.addWidget(self.update_temp_limits_button)

        self.oven_check_interval_input = QLineEdit()
        self.oven_check_interval_button = QPushButton("Überprüfungsintervall einstellen")
        self.oven_check_interval_button.clicked.connect(self.set_oven_check_interval)
        self.layout.addWidget(QLabel("Überprüfungsintervall für den Ofen (in Sekunden):"))
        self.layout.addWidget(self.oven_check_interval_input)
        self.layout.addWidget(self.oven_check_interval_button)

        self.label_fire_status = QLabel("Ofenstatus: Warte auf Update...")
        self.label_fire_status.setFont(QFont("Arial", 10))
        self.layout.addWidget(self.label_fire_status)

    def update_temperature_label(self, temperature):
        self.label_temperature.setText(f"Aktuelle Temperatur: {temperature:.2f} °C")

    def update_temperature_limits(self):
        try:
            high_limit = float(self.temp_limit_high.text())
            medium_limit = float(self.temp_limit_medium.text())
            low_limit = float(self.temp_limit_low.text())
            self.client.set_temperature_limits(high_limit, medium_limit, low_limit)

            self.label_high_limit.setText(f"Höchste Temperatur (aktualisiert): {high_limit}")
            self.label_medium_limit.setText(f"Mittlere Temperatur (aktualisiert): {medium_limit}")
            self.label_low_limit.setText(f"Niedrige Temperatur (aktualisiert): {low_limit}")

            QMessageBox.information(self.main_window, "Das hat geklappt", "Temperaturen wurden aktualisiert.")
        except ValueError:
            QMessageBox.warning(self.main_window, "Das hat leider nicht geklappt", "Falsche Eingabe")

    def set_oven_check_interval(self):
        try:
            interval = int(self.oven_check_interval_input.text())
            self.oven_watcher.set_check_interval(interval)
            QMessageBox.information(self.main_window, "Erfolg", "Überprüfungsintervall aktualisiert.")
        except ValueError:
            QMessageBox.warning(self.main_window, "Fehler", "Ungültige Eingabe.")

    def update_fire_status_label(self, status):
        self.label_fire_status.setText(f"Ofenstatus: {status}")
        if status == "Achtung: Das Feuer im Ofen ist niedrig!":
            QMessageBox.warning(self.main_window, "Ofenstatus Warnung", "Achtung: Das Feuer im Ofen ist niedrig!")



    def show(self):
        self.main_window.show()

if __name__ == "__main__":
    client_gui = MyClientGUI()
    client_gui.show()
    sys.exit(client_gui.app.exec_())



