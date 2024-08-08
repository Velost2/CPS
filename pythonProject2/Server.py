from socket import *
import threading
import os
import time
import Adafruit_ADS1x15
from time import sleep
import numpy as np
from threading import Timer
import matplotlib.pyplot as plt

adc_channel_0 = 0


class MyTask():
    def __init__(self, timer_periode, hFunction):
        self.timer_periode = timer_periode
        self.hFunction = hFunction
        self.thread = Timer(self.timer_periode, self.handle_function)

    def handle_function(self):
        self.hFunction()
        self.thread = Timer(self.timer_periode, self.handle_function)
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
        print("Spannung", self.voltage_mess)
        temp = np.log((10000 / self.voltage_mess) * (3.3 - self.voltage_mess))
        temp = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * np.power(temp, 2))) * temp)
        self.temperatur = temp - 273.13
        print("Temperatur: %s °C" % (self.temperatur))

    def update_new_data(self):
        if self.xs == []:
            self.xs.append(1)
        else:
            self.xs.append(self.xs[-1] + 1)
        self.ys.append(self.temperatur)

    def measure_and_update(self):
        self.meas_temperature(adc_channel_0)
        self.update_new_data()

class MyServer:
    echo_port = 5068    #port festlegen
    buffsize = 1024  #Bufsize von 1024 ist für einfache Nachrichten genug

    def __init__(self):
        self.data_recv = None #variabeln für das senden und empfangen festlegen
        self.data_send = None
        self.socket_connection = socket(AF_INET, SOCK_STREAM)
        self.socket_connection.bind(("", self.echo_port))
        self.socket_connection.listen(1)
        print("Server is running")
        print("Host name: ", gethostname())
        print("Host IP: ", gethostbyname(gethostname()))
        self.conn, (self.remotehost, self.remoteport) = self.socket_connection.accept() #verbindung initiieren
        print("connected with %s %s" % (self.remotehost, self.remoteport))
        self.thread_recv = threading.Thread(target=self.worker_recv) #threads erstellen
        self.thread_send = threading.Thread(target=self.worker_send)
        self.laufzeit = 30 #laufzeit festlegen
        self.exit = False #abbruch/beenden variable festlegen
        self.thread_recv.start() #threads starten
        self.thread_send.start()

    def worker_recv(self):
        while not self.exit:
            self.data_recv = self.conn.recv(self.buffsize)
            if self.data_recv != None:
                print("Server bekommt Nachricht %s" % (self.data_recv))
                if self.data_recv == b'stop':
                    self.laufzeit = 1
                    print("Verbindung wurde getrennt")

    def worker_send(self): #funktion, die das senden der daten handhabt
        while self.exit == False: #solange exit==False unendlich schleife
            print("Type message: ") #Code der mittels input das austauchen von nachrichten ermöglicht
            message=input()
            self.data_send = message
            self.data_send = self.data_send
            self.conn.send(self.data_send.encode())
            if message == "stop":
                self.laufzeit=1
                print("verbindung getrennt")
            time.sleep(1)

    def stopp_connect(self):  # funktion zum beenden der threads
        self.exit = True
        if threading.current_thread() is threading.main_thread():
            self.thread_recv.join()
            self.thread_send.join()
        self.socket_connection.close()


server = MyServer()
while True:
    if server.laufzeit==1:
        break
server.stopp_connect()
print("Erfolg auf Server side")
