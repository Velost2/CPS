from socket import *
import threading
import os
import time


class MyServer:
    echo_port = 5007    #port festlegen
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

    def worker_recv(self): #funktion, die das empfangen der daten handhabt
        while self.exit == False: #solange exit==False unendlich schleife
            self.data_recv = self.conn.recv(self.buffsize)
            if self.data_recv != None:#data_recv muss hier none sein, da kein wert übergeben wird
                print("Server bekommt nachricht %s" % (self.data_recv))
                if self.data_recv == b'stop':  # Annahme, dass 'stop' eine Bytesequenz ist
                    self.laufzeit=1
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
