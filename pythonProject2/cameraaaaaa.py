import time
from picamera import PiCamera
import numpy as np

# Initialisieren der Kamera
camera = PiCamera()
camera.resolution = (128, 112)

def is_fire_low(image):
    """Bestimmt, ob das Feuer im Ofen niedrig brennt, basierend auf der Helligkeit in einem bestimmten Bereich des Bildes."""
    # Hier wählen Sie einen spezifischen Bereich des Bildes aus, z.B. den mittleren Teil
    region_of_interest = image[40:80, 44:84]  # Beispielbereich
    # Schwellenwert anpassen
    return np.mean(region_of_interest) < 80  # Schwellenwert für niedriges Feuer

try:
    while True:
        # Erfasse ein Bild und konvertiere es in ein NumPy-Array
        output = np.empty((112, 128, 3), dtype=np.uint8)
        camera.capture(output, 'rgb')

        # Überprüfe, ob das Feuer niedrig brennt
        if is_fire_low(output):
            print("Achtung: Das Feuer im Ofen ist niedrig!")
        else:
            print("Der Ofen brennt normal.")

        time.sleep(5)  # Warte 5 Sekunden bevor der nächsteDurchl
        # auf beginnt

except KeyboardInterrupt:
    print("Programm beendet.")
