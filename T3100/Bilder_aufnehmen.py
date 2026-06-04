from picamera2 import Picamera2
import time
import os

# ------------------ CONFIG ------------------
SAVE_DIR = "/home/studienarbeit/projektarbeit_bilder/test_new"
NUM_PICTURES = 300
NUM_START = 1
PAUSE_BETWEEN = 5  # Sekunden zwischen den Bildern

# ------------------ INITIALISIERUNG ------------------
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

# ------------------ Dauerautofokus aktivieren ------------------
picam2.set_controls({"AfMode": 2})  # Continuous AF
time.sleep(0.5)  # AF starten lassen

# ------------------ SERIENAUFNAHME ------------------
for i in range(NUM_START, NUM_START + NUM_PICTURES):
    filename = f"picture_{i:03d}.jpg"
    full_path = os.path.join(SAVE_DIR, filename)

    # Bild aufnehmen (AF läuft automatisch im Preview)
    picam2.switch_mode_and_capture_file(still_config, full_path, wait=True)
    print(f"Captured {filename}")

    # Pause zwischen den Bildern
    time.sleep(PAUSE_BETWEEN)

# ------------------ ENDE ------------------
picam2.stop()
print("Serienaufnahme abgeschlossen!")
