from socket import *
import threading
import time
import pigpio
from collections import deque
from os import system

# GPIO-Pins für den Schrittmotor
steppins = [17, 18, 27, 22]
# Sequenz für den Schrittmotor (Vollschritt)
fullstepsequence = (
    (1, 0, 1, 0),
    (0, 1, 1, 0),
    (0, 1, 0, 1),
    (1, 0, 0, 1))

class MyServer:
    echo_port = 5068  # Port für die Verbindung
    buffsize = 1024  # Puffergröße von 1024     Bytes für empfangene Nachrichten ausreichend

    def __init__(self):
        self.exit = False
        self.laufzeit = 30  # Laufzeit für das Programm, bevor es beendet werden kann

        pi = pigpio.pi()
        # Initialisierung des Schrittmotors mit Pins und Sequenz
        self.motor = StepperMotor(pi, steppins, fullstepsequence)
        self.motor.set_stepper_delay(900)

        self.recv_steps = None
        self.data_recv = None
        self.data_send = None

        self.socket_connection = socket(AF_INET, SOCK_STREAM)
        self.socket_connection.bind(("", self.echo_port))
        self.socket_connection.listen(1)

        # Serverinformationen
        print("Server is running")
        print("Host name: ", gethostname())
        print("Host IP: ", gethostbyname(gethostname()))

        self.conn, (self.remotehost, self.remoteport) = self.socket_connection.accept()
        print("Connected with %s %s" % (self.remotehost, self.remoteport))

    def worker_recv(self):
        # Funktion für den Empfang von Daten vom Client
        while not self.exit:
            self.data_recv = self.conn.recv(self.buffsize)
            if self.data_recv:
                print("Server bekommt Nachricht %s" % self.data_recv)
                if self.data_recv == b'stop':
                    print("Stop-Nachricht empfangen")
                    self.laufzeit = 1
                    print("Verbindung wurde getrennt")
                elif self.data_recv.isdigit():
                    print("Zahl empfangen:", int(self.data_recv))
                    self.recv_steps = int(self.data_recv)
                    self.motor.set_steps_to_perform(self.recv_steps)

    def worker_send(self):
        # Funktion für das Senden von Daten an den Client
        while not self.exit:
            print("Type message: ")
            message = input()
            self.data_send = message
            self.socket_connection.send(self.data_send.encode())
            if message == "stop":
                self.laufzeit = 1
                print("Verbindung getrennt")
            time.sleep(1)

    def stopp_connect(self):
        # Funktion zum Beenden der Threads und Schließen der Socket-Verbindung
        self.exit = True
        self.socket_connection.close()

    def run_motor(self):
        # Funktion für die Ausführung des Schrittmotors
        while not self.exit:
            self.motor.perform_steps()
            time.sleep(0.01)

class StepperMotor:
    def __init__(self, pi, pins, sequence):
        if not isinstance(pi, pigpio.pi):
            raise TypeError("Der Daemon pigpio.pi ist nicht instanziert!")
        for pin in pins:
            pi.set_mode(pin, pigpio.OUTPUT)
        self.deque = deque(sequence)
        self.pi = pi
        self.__delay_after_step = None
        self.lock = threading.Lock()
        self.steps_to_perform = None

    def set_steps_to_perform(self, steps):
        with self.lock:
            self.steps_to_perform = steps

    def perform_steps(self):
        with self.lock:
            if self.steps_to_perform is not None:
                for _ in range(self.steps_to_perform):
                    self.deque.rotate(-1)
                    self.do_step_and_delay(self.deque[0])
                self.steps_to_perform = None

    def set_stepper_delay(self, step_freq):
        if 0 < step_freq < 1500:
            self.__delay_after_step = 1 / step_freq

    def do_counterclockwise_step(self):
        with self.lock:
            self.deque.rotate(-1)
            self.do_step_and_delay(self.deque[0])

    def do_clockwise_step(self):
        with self.lock:
            self.deque.rotate(1)
            self.do_step_and_delay(self.deque[0])

    def do_step_and_delay(self, step):
        nr = 0
        for pin in steppins:
            self.pi.write(pin, step[nr])
            nr += 1
        time.sleep(self.__delay_after_step)

    def disable_stepper_motor(self, pins):
        for pin in pins:
            self.pi.write(pin, 0)

# Deaktivierung des pigpiod-Daemons und erneutes Starten
system("sudo systemctl disable pigpiod")
time.sleep(0.5)
system("sudo systemctl start pigpiod")

# Instanzierung des Servers und Starten der Threads
server = MyServer()
recv_thread = threading.Thread(target=server.worker_recv)
send_thread = threading.Thread(target=server.worker_send)
motor_thread = threading.Thread(target=server.run_motor)

recv_thread.start()
send_thread.start()
motor_thread.start()

# Warten auf das Ende der Threads und Beenden des Servers
recv_thread.join()
send_thread.join()
motor_thread.join()

server.stopp_connect()
print("Erfolg auf Server-Seite")
