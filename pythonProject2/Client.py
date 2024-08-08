from socket import *
import threading
import os
import time
import Adafruit_ADS1x15
import numpy as np
import matplotlib.pyplot as plt

adc_channel_0 = 0


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


class MyTemp():
    def __init__(self, gain, sps):
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

    def update_new_data(self):
        if self.xs == []:
            self.xs.append(1)
        else:
            self.xs.append(self.xs[-1] + 1)
        self.ys.append(self.temperatur)

    def measure_and_update(self):
        self.meas_temperature(adc_channel_0)
        self.update_new_data()


class MyClient:
    server_port = 5068  # port festlegen
    bufsize = 1024  # Bufsize von 1024 ist für einfache Nachrichten genug
    host = "192.168.178.124"  # host (raspberry) festlegen

    def __init__(self, temp_instance):
        self.last_sent_temperature = None
        self.data_recv = None  # variabeln für das senden und empfangen festlegen
        self.data_send = None
        self.host = "192.168.178.124"
        self.socket_connection = socket(AF_INET, SOCK_STREAM)
        self.temp_instance = temp_instance  # Referenz auf die Instanz von MyTemp
        self.thread_recv = threading.Thread(target=self.worker_recv)  # threads erstellen
        self.thread_send = threading.Thread(target=self.worker_send)
        self.laufzeit = 30  # laufzeit festlegen
        self.socket_connection.connect((self.host, self.server_port))  # verbindung initiieren
        print("Verbunden mit dem server: %s" % (self.host))
        self.exit = False  # abbruch/beenden variable festlegen
        self.thread_recv.start()  # threads starten
        self.thread_send.start()

    def worker_recv(self):  # funktion, die das empfangen der daten handhabt
        while not self.exit:  # solange exit==False unendlich schleife
            self.data_recv = self.socket_connection.recv(self.bufsize)
            if self.data_recv != None:  # data_recv muss hier none sein, da kein wert übergeben wird
                print("Client bekommt Nachricht %s" % (self.data_recv))
                if self.data_recv == b'stop':  # wenn die nachricht "stop" enthält wird die while schleife geschlossen
                    self.data_send = "stop"
                    self.socket_connection.send(self.data_send.encode())
                    self.laufzeit = 1
                    print("Verbindung wurde getrennt")

    def worker_send(self):
        previous_temperature_category = None #category wird erstellt, um vergleichen zu können

        while not self.exit:
            self.temp_instance.measure_and_update()  # Temperaturmessung und Update durchführen

            if self.temp_instance.temperatur is not None:
                print("Current Temperature:", self.temp_instance.temperatur)
                print("Last Sent Temperature:", self.last_sent_temperature)

                # testen, ob sich die temperaturen unterscheiden
                if (
                        self.last_sent_temperature is None
                        or round(self.temp_instance.temperatur) != round(self.last_sent_temperature)
                ):
                    #Wenn bestimmte temperatur erreicht wird, wird eine category festgelegt
                    if self.temp_instance.temperatur >= 30:
                        current_temperature_category = "300"
                    elif self.temp_instance.temperatur >= 27:
                        current_temperature_category = "250"
                    elif self.temp_instance.temperatur >= 20:
                        current_temperature_category = "200"
                    else:
                        current_temperature_category = "normal"

                    print("Current Category:", current_temperature_category)
                    print("Previous Category:", previous_temperature_category)

                    # Überprüfen, ob sich die category geändert hat
                    if current_temperature_category != previous_temperature_category:
                        print("Temperatur: %s °C" % (self.temp_instance.temperatur))
                        print("Type message: %s" % current_temperature_category)
                        #temperature category wird zu data send und an den server mit dem motor gesendet
                        self.data_send = current_temperature_category
                        self.socket_connection.send(self.data_send.encode())
                        self.last_sent_temperature = round(self.temp_instance.temperatur)
                        previous_temperature_category = current_temperature_category

                        if self.data_send == "stop":
                            self.laufzeit = 1
                            print("Verbindung getrennt")

                time.sleep(5)

    def stopp_connect(self):  # funktion zum beenden der threads
        self.exit = True
        if threading.current_thread() is threading.main_thread():
            self.thread_recv.join()
            self.thread_send.join()
        self.socket_connection.close()


gain = 1
sps = 64
temp_sense = MyTemp(gain, sps)
client = MyClient(temp_sense)  # Die Instanz von MyTemp wird an MyClient übergeben
task_meas = MyTask(1, temp_sense.measure_and_update, duration=30)
task_meas.start()

try:
    while True:
        pass
except KeyboardInterrupt:
    task_meas.cancel()

plt.plot(temp_sense.xs, temp_sense.ys)
plt.yscale('linear')
plt.ylabel('Temperatur in [°C]')
plt.xlabel("Zeit in Sekunden")
plt.show()
