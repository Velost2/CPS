from socket import *
import threading
import os
import time


class MyClient:
    server_port = 5007  # port festlegen
    bufsize = 1024  # Bufsize von 1024 ist für einfache Nachrichten genug
    host = "192.168.178.128"  # host (raspberry) festlegen

    def __init__(self):
        self.data_recv = None  # variabeln für das senden und empfangen festlegen
        self.data_send = None
        self.socket_connection = socket(AF_INET, SOCK_STREAM)
        self.thread_recv = threading.Thread(
            target=self.worker_recv
        )  # threads erstellen
        self.thread_send = threading.Thread(target=self.worker_send)
        self.laufzeit = 30  # laufzeit festlegen
        self.socket_connection.connect(
            (self.host, self.server_port)
        )  # verbindung initiieren
        print("Verbunden mit dem server: %s" % (self.host))
        self.exit = False  # abbruch/beenden variable festlegen
        self.thread_recv.start()  # threads starten
        self.thread_send.start()

    def worker_recv(self):  # funktion, die das empfangen der daten handhabt
        while not self.exit:  # solange exit==False unendlich schleife
            self.data_recv = self.socket_connection.recv(self.bufsize)
            if (
                self.data_recv != None
            ):  # data_recv muss hier none sein, da kein wert übergeben wird
                print("Client bekommt nachricht %s" % (self.data_recv))
                if (
                    self.data_recv == b"stop"
                ):  # wenn die nachricht "stop" enthält wird die while schleife geschlossen
                    self.data_send = "stop"
                    self.socket_connection.send(self.data_send.encode())
                    self.laufzeit = 1
                    print("Verbindung wurde getrennt")

    def worker_send(self):
        while not self.exit:
            print("Type message: ")
            message = input()
            self.data_send = (
                message  # Hier setzen Sie self.data_send auf die eingegebene Nachricht
            )
            self.socket_connection.send(self.data_send.encode())
            if message == "stop":
                self.laufzeit = 1
                print("Verbindung getrennt")
            time.sleep(1)

    def stopp_connect(self):  # funktion zum beenden der threads
        self.exit = True
        if threading.current_thread() is threading.main_thread():
            self.thread_recv.join()
            self.thread_send.join()
        self.socket_connection.close()


client = MyClient()
while True:
    if client.laufzeit == 1:
        break
client.stopp_connect()
print("Erfolg auf client side")
