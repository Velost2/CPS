import tkinter as tk
from socket import *
import threading
import time
import pigpio
from collections import deque
from os import system

# GPIO-Pins für den Schrittmotor test
steppins = [17, 18, 27, 22]
# Sequenz für den Schrittmotor (Vollschritt)
fullstepsequence = (
    (1, 0, 1, 0),
    (0, 1, 1, 0),
    (0, 1, 0, 1),
    (1, 0, 0, 1))

class MyServer:
    echo_port = 5068
    buffsize = 1024

    def __init__(self):
        self.exit = False
        self.laufzeit = 30
        pi = pigpio.pi()
        self.motor = StepperMotor(pi, steppins, fullstepsequence)
        self.motor.set_stepper_delay(900)
        self.recv_steps = None
        self.data_recv = None
        self.data_send = None
        self.socket_connection = socket(AF_INET, SOCK_STREAM)
        self.socket_connection.bind(("", self.echo_port))
        self.socket_connection.listen(1)
        self.connected = False  # Flag für Verbindungsstatus
        self.server_started = False  # Flag für Server-Status

    def worker_recv(self):
        self.recv_steps = -1  # Initialisierung mit einem Wert außerhalb des erwarteten Bereichs
        while not self.exit:
            # Wait for a new connection
            self.conn, (self.remotehost, self.remoteport) = self.socket_connection.accept()
            self.connected = True
            print("Verbunden mit %s %s" % (self.remotehost, self.remoteport))

            while not self.exit:
                try:
                    self.data_recv = self.conn.recv(self.buffsize)
                    if not self.data_recv:
                        print("Client disconnected")
                        self.conn.close()
                        self.connected = False
                        break

                    print("Server bekommt Nachricht %s" % self.data_recv)

                    if self.data_recv.isdigit():
                        received_steps = int(self.data_recv)
                        print(f"Empfangene Schritte: {received_steps}, Vorherige Schritte: {self.recv_steps}")
                        if received_steps < self.recv_steps:
                            print("Motor rückwärts")
                            for received_steps in range (received_steps):
                                self.motor.do_counterclockwise_step()
                        else:
                            print("Motor vorwärts")
                            for received_steps in range (received_steps):
                                self.motor.do_clockwise_step()
                        self.recv_steps = received_steps

                except OSError as e:
                    print(f"Socket error: {e}")
                    if self.conn:
                        self.conn.close()
                    self.connected = False
                    break

    def stopp_connect(self):
        self.exit = True
        self.socket_connection.close()


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

    def do_counterclockwise_step(self):
        self.deque.rotate(-1)  # Einen Schritt rückwärts in der Sequenz
        self.do_step_and_delay(self.deque[0])

    def do_clockwise_step(self):
        self.deque.rotate(1)  # Einen Schritt vorwärts in der Sequenz
        self.do_step_and_delay(self.deque[0])

    def set_stepper_delay(self, step_freq):
        if 0 < step_freq < 1500:
            self.__delay_after_step = 1 / step_freq

    def do_step_and_delay(self, step):
        nr = 0
        for pin in steppins:
            self.pi.write(pin, step[nr])
            nr += 1
        time.sleep(self.__delay_after_step)

def start_server():
    global server, recv_thread
    server = MyServer()
    recv_thread = threading.Thread(target=server.worker_recv)
    recv_thread.start()
    server.server_started = True


def stop_server():
    global server, recv_thread
    server.stopp_connect()
    server.exit = True  # Setze das Exit-Flag für den Motor
    recv_thread.join()
    server.server_started = False  # Setze den Server-Status auf gestoppt


def gui_update():
    global server, status_label, start_button, stop_button
    if server and server.connected:
        status_label.config(text="Verbunden")
        status_label.config(fg="green")
    else:
        status_label.config(text="Warte auf Verbindung...")
        status_label.config(fg="black")

    if server and server.server_started:
        start_button.config(state="disabled")
        stop_button.config(state="active")
        server_status_label.config(text="Server gestartet")
    else:
        start_button.config(state="active")
        stop_button.config(state="disabled")
        server_status_label.config(text="Server gestoppt")

    root.after(1000, gui_update)

root = tk.Tk()
root.title("Raspberry Pi Server GUI")

start_button = tk.Button(root, text="Server starten", command=start_server)
start_button.pack()

stop_button = tk.Button(root, text="Server beenden", command=stop_server, state="disabled")
stop_button.pack()

status_label = tk.Label(root, text="Warte auf Verbindung...", font=("Helvetica", 16))
status_label.pack(pady=20)

server_status_label = tk.Label(root, text="", font=("Helvetica", 12))
server_status_label.pack(pady=10)

server = None
recv_thread = None
motor_thread = None

gui_update()

root.mainloop()
