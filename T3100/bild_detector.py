# Import Libraries
from picamera2 import Picamera2           # Kamera-Modul
from libcamera import controls
import time                               # Wartezeiten
import os                                 # Dateipfade
from ultralytics import YOLO              # YOLO-Modell
from datetime import datetime             # Für eindeutige Zeitstempel
from gpiozero import Button

from luma.core.interface.serial import i2c #OLED-Bildschirm
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw


# OLED initialisieren
serial = i2c(port=1, address=0x3C)
oled = ssd1306(serial, width=128, height=32)
image_counter = 0

def oled_show(lines):
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    y = 0
    for line in lines[:2]:   # max. 2 Zeilen bei 128x32
        draw.text((0, y), line, fill=255)
        y += 16

    oled.display(image)
    
def oled_clear():
    image = Image.new("1", (oled.width, oled.height))
    oled.display(image)

# OLED Reset beim Programmstart
oled_clear()
time.sleep(0.2)


# Konfiguration der Pfade
SAVE_DIR = "/home/studienarbeit/yolo/taken_pictures"
MODEL_PATH = "/home/studienarbeit/yolo/best_ncnn_model"
BUTTON_PIN = 17     # GPIO Pin 17

button = Button(BUTTON_PIN)

# YOLO-Modell starten
try:
    model = YOLO(MODEL_PATH)
    print("YOLO-Modell erfolgreich geladen.")
except FileNotFoundError:
    print(f"FEHLER: Modellpfad nicht gefunden: {MODEL_PATH}")
    exit()
    
# Kamera initialisieren
picam2 = Picamera2()
capture_config = picam2.create_still_configuration(main={"size": (1280, 960)})
picam2.configure(capture_config)
picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
picam2.start()
time.sleep(1)

print("\nProgramm gestartet.")
print("Drücke ENTER, um ein Bild aufzunehmen.")
print("Das Programm läuft endlos weiter, bis beim Launcher manuelle auf 'STOP' gedrückt wird")
oled_show(["System bereit", "Warte auf Knopf"])

# Start der Endlosschleife: Warten -> Bild aufnehmen -> Bild analysieren
while True:
    print("-> Warte auf Knopfdruck...")
    button.wait_for_press()
    print("Knopf gedrückt! Aufnahme startet...")
        
        
    # 1. Dateiname mit Zeitstempel erzeugen
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"picture_{timestamp}.jpg"
    full_path = os.path.join(SAVE_DIR, filename)
        
    # 2. Bild aufnehmen
    picam2.autofocus_cycle()
    time.sleep(1)
     
    picam2.capture_file(full_path)
    image_counter += 1
    
    print(f"\n Bild aufgenommen und gespeichert in: {full_path}")
        
    # 3. YOLO-Analyse durchführen
    results = model.predict(
        source = full_path,
        conf=0.5,
        save=True
    )
        
    # 4. Ergebnis ausgeben
    for result in results:
        boxes = result.boxes
        class_names = result.names
            
        print(f"\nBild: {os.path.basename(result.path)}")
        print(f"Anzahl erkannter Objekte: {len(boxes)}")
            
        if len(boxes) == 0:
            oled_show(["Keine Objekte", f"erkannt                             #{image_counter}"])
            
        for box in boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            predicted_class = class_names[class_id]
                
            print(f"  -> Klasse: {predicted_class}, Konfidenz: {confidence:.2f}")
                
            # OLED-Ausgabe
            oled_show([
                f"{predicted_class}",
                f"Conf:{confidence:.2f}                          #{image_counter}"
            ])
            
        print("Analyse abgeschlossen.\n")

