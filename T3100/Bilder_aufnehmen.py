from picamera2 import Picamera2
import time
import os

# Configuration
SAVE_DIR = "/home/studienarbeit/projektarbeit_bilder/test_new"
NUM_PICTURES = 300
NUM_START = 1
PAUSE_BETWEEN = 5  # Zeit in Sekunden zwischen den Aufnahmen

# Initialisierung
picam2 = Picamera2()

# Preview-Konfiguration
preview_config = picam2.create_preview_configuration(
    main={"size": (2200, 1650)}
)

# Still-Konfiguration (für die Aufnahmen)
still_config = picam2.create_still_configuration(
    main={"size": (2200, 1650)}
)

# Konfigurieren und Preview starten
picam2.configure(preview_config)
picam2.start(show_preview=True)
time.sleep(2)  # kurze Stabilisierung der Kamera

# Dauerautofokus aktivieren
picam2.set_controls({"AfMode": 2})  # Durchgehender Autofokus
time.sleep(0.5)  # Autofokus starten lassen

# Serienaufnahme
for i in range(NUM_START, NUM_START + NUM_PICTURES):
    filename = f"picture_{i:03d}.jpg"
    full_path = os.path.join(SAVE_DIR, filename) 
    picam2.switch_mode_and_capture_file(still_config, full_path, wait=True) # Bild aufnehmen (AF läuft automatisch im Preview)
    print(f"Captured {filename}")
    time.sleep(PAUSE_BETWEEN) # Pause zwischen den Bildern

picam2.stop()
