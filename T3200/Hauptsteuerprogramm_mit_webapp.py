import threading
import time
import cv2
import datetime
import os
import signal
from flask import Flask, render_template, Response, jsonify, send_from_directory, session, redirect, url_for, request
from stepper import Stepper
from ultralytics import YOLO
from picamera2 import Picamera2
from gpiozero import Button

# --- Import OLED ---
from luma.core.interface.serial import i2c 
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw

# --- FLASK Setup ---
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'k231p4jpoidsajfkwq093ALKDSfapdfEL234091'
DASHBOARD_PASSWORD = "nudel"
last_events = []    # Liste für die Web-Anzeige
latest_frame = None # Globaler Buffer für Video-Stream

# --- CONFIG ---
MODEL_PATH = "best.onnx"
IMAGE_SIZE = (320, 240) # Größe für die KI (muss klein bleiben für Speed)
DISPLAY_SIZE = (1280, 960) # Größe für das Fenster (hier kannst du variieren)
MOTOR_SPEED = 12
SCHRANKE_SPEED = 12
CONF_LEVEL = 0.25
MIN_CONF_LOGIK = 0.8
BUTTON_PIN = 21 #GPIO-Pin 21

# --- OLED initialisieren ---
serial = i2c(port=1, address=0x3C)
oled = ssd1306(serial, width=128, height=32)

def oled_update_display(counts):
    """ Erstellt eine Tabelle mit 4 Spalten und zentriertem Text """
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    
    # 1. Spalten-Definition (Mittelpunkte der 4 Spalten bei 128px Breite)
    # Spalte 1: 0-31 (Mitte 16), Spalte 2: 32-63 (Mitte 48), usw.
    col_centers = [16, 48, 80, 112]
    
    # 2. Header und zugehörige Werte definieren
    headers = ["Norm", "Brok", "Gem", "Pipe"]
    values = [str(counts["0"]), str(counts["1"]), str(counts["2"]), str(counts["3"])]
    
    for i in range(4):
        # Text-Breite berechnen, um ihn mittig zu platzieren
        # (Standard-Schriftart ist ca. 6 Pixel breit pro Zeichen)
        header_text = headers[i]
        value_text = values[i]
        
        # Header zentrieren (Obere Zeile y=0)
        # Wir nutzen anchor="mt" (Middle-Top), falls Pillow aktuell ist, 
        # sonst berechnen wir die x-Position manuell:
        w_h = draw.textlength(header_text) if hasattr(draw, 'textlength') else len(header_text) * 6
        draw.text((col_centers[i] - w_h/2, 0), header_text, fill=255)
        
        # Zahlen zentrieren (Untere Zeile y=16)
        w_v = draw.textlength(value_text) if hasattr(draw, 'textlength') else len(value_text) * 6
        draw.text((col_centers[i] - w_v/2, 16), value_text, fill=255)
    
    oled.display(image)
    
def oled_clear():
    image = Image.new("1", (oled.width, oled.height))
    oled.display(image)

def trigger_shutdown():
    """ Sendet ein SIGINT (entspricht Strg+C) an den aktuellen Prozess """
    os.kill(os.getpid(), signal.SIGINT)

def motor_ablauf_thread(cls_id): # NEU: Eigene Funktion für den Thread
    global motor_laeuft, schranke_offen, nudel_in_verarbeitung
    
    # 1s weiterfahren, Stopp, Schranke (dein bisheriger Ablauf)
    time.sleep(1) # Blockiert jetzt nur diesen Thread, nicht den Stream
    motor_laeuft = False
    
    if cls_id == 0:
        schranke.step(256)
        schranke_offen = True
        motor_laeuft = True
        time.sleep(10)
        motor_laeuft = False
        time.sleep(0.2)
        schranke.step(-256)
        schranke_offen = False
    else:
        motor_laeuft = True
        time.sleep(10)
    
    motor_laeuft = True
    # Warten, bis die Nudel sicher aus dem Sichtfeld ist, dann wieder freigeben
    time.sleep(2) 
    nudel_in_verarbeitung = False # NEU: Erst hier wieder auf False setzen

# --- Button initialisieren ---
button = Button(BUTTON_PIN)
button.when_pressed = trigger_shutdown

# --- Zähler initialisieren ---
class_counts = {
    "0": 0, # noodle
    "1": 0, # broken_noodle
    "2": 0, # false_noodle_type_gemelli
    "3": 0  # false_noodle_type_Pipe_Rigatte
}

# Verzeichnis für Bilder erstellen
if not os.path.exists('static/captures'):
    os.makedirs('static/captures')

# --- MOTOREN ---
# Fliessband initialisieren
motor = Stepper(2048, 5, 6, 13, 19)
motor.set_speed(MOTOR_SPEED)

# Schranke initialisieren
schranke = Stepper(2048, 24, 25, 12, 16)
schranke.set_speed(SCHRANKE_SPEED)

# Status-Variablen für die Logik
band_aktiv = True               # Grundsätzliche Programmschleife
motor_laeuft = True             # Steuert, ob der Motor sich gerade dreht
schranke_offen = False          # Trackt Position für den Abbruch
nudel_in_verarbeitung = False   # Verhindert, dass eine Nudel mehrfach triggert

@app.before_request # Prüft vor jeder Anfrage, ob Nutzer bereits eingeloggt ist
def check_login():
    # Erlaube Zugriff auf die Login-Seite und das Manifest ohne Login
    if request.endpoint in ['login', 'serve_manifest', 'static']:
        return
    
    # Wenn nicht eingeloggt, leite zur Login-Seite um
    if 'logged_in' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Falsches Passwort!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Flask Routen
@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    global latest_frame
    while True:
        if latest_frame is not None:
            ret, buffer = cv2.imencode('.jpg', latest_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/events')
def get_events():
    return jsonify({
        "events":last_events[-10:],
        "counts": class_counts
    }) # Sendet die letzten 10 Events und class_counts

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'manifest.json')

def fliesband_logik(): # Prüft, auf Programmende und kurzzeitigem Stopp
    while band_aktiv:
        if motor_laeuft:
            motor.step(-64)
        else:
            time.sleep(0.1) # CPU entlasten wenn Band steht
    motor.stop()

def main_loop():
    global latest_frame, motor_laeuft, schranke_offen, nudel_in_verarbeitung, band_aktiv
    
    model = YOLO(MODEL_PATH, task="detect")
    picam2 = Picamera2()
    config = picam2.create_still_configuration(main={"size": IMAGE_SIZE})
    picam2.configure(config)
    picam2.start()

    oled_update_display(class_counts)

    print("[System] Starte KI und Kamera...")

    while band_aktiv:
        frame_rgb = picam2.capture_array()
        frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        results = model.predict(frame, conf=0.25, verbose=False)

        # Inferenzzeit auslesen und drucken 
        inference_time = results[0].speed['inference'] 
        print(f"Inferenzzeit: {inference_time:.2f} ms")
        
        display_frame = frame.copy()
        detections = results[0].boxes
        valid_detections = [box for box in detections if float(box.conf[0]) > MIN_CONF_LOGIK]

    

        # Zeichnen der Boxen für Web-Stream    
        for box in detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label_name = model.names[cls]
            
            # Farbe wählen (Grün für gute Nudeln, Rot für Fehler, Grau für niedrige Confidence)
            if conf > MIN_CONF_LOGIK:
                color = (0, 255, 0) if cls == 0 else (0, 0, 255)
                thickness = 2
            else:
                color = (120, 120, 120)
                thickness = 1
            
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(display_frame, f"{label_name} {conf:.2f}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Logik-Ablauf 
        if len(valid_detections) > 0 and not nudel_in_verarbeitung:
            nudel_in_verarbeitung = True
            box = valid_detections[0]
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])

            # Zaehler hochzählen
            class_counts[str(cls_id)] += 1

            #oled update bei erkennung
            oled_update_display(class_counts)

            # Event für Web-App speichern
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            last_events.append({"time": timestamp, "label": label, "conf": round(conf*100, 1)})

            # 1s weiterfahren, Stopp, Schranke (dein Ablauf)
            threading.Thread(target=motor_ablauf_thread, args=(cls_id,), daemon=True).start()
            

        
        # Frame für den Web-Stream aktualisieren
        latest_frame = display_frame

    picam2.stop()

# --- START ---
if __name__ == '__main__':
    try:
        # 1. Fließband-Thread
        threading.Thread(target=fliesband_logik, daemon=True).start()
        
        # 2. KI-Thread
        threading.Thread(target=main_loop, daemon=True).start()
        
        # 3. Webserver starten
        print(f"[Web] Dashboard erreichbar unter http://127.0.0.1:5000 und extern via Cloudfare")
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

    # neu: Sauberer Abbruch bei CTRL+C, um Motoren zu stoppen
    except KeyboardInterrupt:
        print("\n[System] Abbruch durch Benutzer...")
    finally:
        band_aktiv = False
        motor_laeuft = False
        time.sleep(0.5)
        # neu: Falls die Schranke während des Abbruchs noch offen war, zufahren
        if schranke_offen:
            schranke.step(-256)
        motor.stop()
        schranke.stop()
        oled_clear()
        print("[System] Motoren gestoppt. Programm beendet.")