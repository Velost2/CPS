import pigpio                                # GPIO Toolbox zur schnelleren Ansteuerung der IO-Pins
from time import sleep                      # Zeitmethoden
from collections import deque                # Liste als "Schlange" verwalten
from os import system                           # Zugriff auf die Kommandozeile des Raspberry PI
steppins = [17, 18, 27, 22]                     # GPIO Pins der Ansteuerschaltung
fullstepsequence = (                             # Schrittfolge der Ansteuerpins für den
(1, 0, 1, 0), # Vollschrittbetrieb
(0, 1, 1, 0),
(0, 1, 0, 1),
(1, 0, 0, 1)
)
class StepperMotor:
    def __init__(self, pi, pins, sequence): # Konstruktor für das Objekt Steppermotor
        if not isinstance(pi, pigpio.pi): # Prüfe ob der pigpio.pi-Daemon schon gestartet wurde
            raise TypeError("Der Daemon pigpio.pi ist nicht instanziert!")
    for pin in pins: # Alle gültigen Pins werden zu Ausgängen
        pi.set_mode(pin, pigpio.OUTPUT)
    self.deque=deque(sequence) # Tupleliste wird zu einer Queue
    self.pi = pi # Objekt pi ist Teil der Klasse
    self.__delay_after_step = None # Periodendauer der Schrittfolge (geschützt als private)
    def set_stepper_delay(self,step_freq): # Methode zum Setzen der Schrittfrequenz
if (step_freq>0) and (step_freq<1500): # Nur gültige Frequenzen werden zugelassen.
self.__delay_after_step=1/step_freq
def do_counterclockwise_step(self):
self.deque.rotate(-1) # Gehe in der Queue um einen Schritt zurück
self.do_step_and_delay(self.deque[0]) # Übergebe die aktuelle Bitcodierung des Schritts
def do_clockwise_step(self):
self.deque.rotate(1) # Gehe in der Queue um einen Schritt vor
self.do_step_and_delay(self.deque[0]) # Übergebe die aktuelle Bitcodierung des Schritts
def do_step_and_delay(self, step):
nr=0
for pin in steppins: # Setze die Ausangspins gemäß der Bitcodierung
self.pi.write(pin, step[nr])
nr +=1
sleep(self.__delay_after_step) # Wartezeit bis zum nächsten Schritt
def disable_stepper_motor(self,pins):
for pin in pins: # Alle gültigen Pins werden auf off geschaltet
self.pi.write(pin, 0)
system("sudo systemctl disable pigpiod") # Disable des pigpio-daemon über die Kommandozeile
sleep(0.5) # Kleine Wartezeit
system("sudo systemctl start pigpiod") # Starte einen pigpio-daemon über die Kommandozeile
sleep(1.0)
pi = pigpio.pi() # Instanziiere das pi-Objekt
motor = StepperMotor(pi, steppins, fullstepsequence)
motor.set_stepper_delay(900) # Setze Schrittmotorfrequenz auf 900Hz
for steps in range(2048): # Führe 2048 Schritte im Uhrzeigersinn aus.
motor.do_clockwise_step()
for steps in range(2048): # Führe 2048 Schritte im gegen den Uhrzeigersinn aus.
motor.do_counterclockwise_step()
motor.disable_stepper_motor(steppins) # Schalte Ausgänge auf "0"