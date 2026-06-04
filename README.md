# Edge-Computing-System zur Echtzeit-Objekterkennung und mechatronischen Sortierung

Dieses Repository enthält die vollständige Codebasis für die zwei aufeinander aufbauenden Studienarbeiten (Module T3100 und T3200) im Studiengang Mechatronik an der DHBW Stuttgart. 

Das Gesamtziel des Projekts war die Entwicklung eines kostengünstigen, lokalen Edge-AI-Systems auf Basis eines **Raspberry Pi 5**, das verschiedene Nudelsorten sowie beschädigte Nudeln in Echtzeit klassifiziert und über ein automatisiertes Förderband physisch aussortiert.

---

## 📂 T3100: Bilderkennung mit Edge-Device (Grundlagen & KI-Training)

Die erste Arbeit konzentrierte sich auf den Aufbau des Edge-Devices, die Datengenerierung sowie das Training und die lokale Implementierung des Objekterkennungsmodells (**YOLOv8n**). Die Auslösung der Kamera und die Ausgabe der Erkennungsergebnisse erfolgten hier noch rein hardwarebasiert über Taster und OLED-Display.

### Enthaltene Skripte & Funktionen:

* **`Bilder_Aufnehmen.py`**
    * *Zweck:* Automatisierte Datenerfassung für den Bilddatensatz.
    * *Funktion:* Steuert das Raspberry Pi Kamera Modul 3 an, führt vor jeder Aufnahme einen Autofokus-Zyklus (`autofocus_cycle()`) durch und speichert die Bilder mit einem fortlaufenden Index ab, um eine manuelle Belichtung oder Fehlfokusse zu vermeiden.
* **`Splitting_dataset.py`**
    * *Zweck:* Strukturierung des Datensatzes vor dem Training.
    * *Funktion:* Teilt die annotierten Bilddaten mathematisch exakt in ein Verhältnis von **70% Training, 20% Validierung und 10% Testdaten** auf. Es erstellt automatisch die von YOLO geforderte Ordnerstruktur und verschiebt die Bild- und Textdateien (`.txt` mit Bounding-Box-Koordinaten) entsprechend.
* **`train.py`**
    * *Zweck:* Modelltraining via Transfer Learning.
    * *Funktion:* Startet das Training des `yolov8n.pt`-Modells auf einer leistungsstarken externen GPU. Es nutzt die Konfiguration aus der `config.yaml`, um das Modell auf die spezifischen Nudelklassen (z. B. intakte/beschädigte Nudeln) über 100 Epochen hinweg zu trainieren.
* **`bild_detector.py`**
    * *Zweck:* Lokales Hauptprogramm der ersten Projektphase auf dem Raspberry Pi.
    * *Funktion:* Läuft in einer Endlosschleife und wartet auf ein Hardwaresignal via `gpiozero` (Knopfdruck an Pin 17). Nach dem Auslösen wird ein Bild aufgenommen, die lokale KI-Inferenz gestartet und das Ergebnis (Anzahl & Typ der Nudeln) formatiert auf dem per I2C angebundenen **OLED-Display** (`SH1106`) ausgegeben.

---

## 📂 T3200: Mechatronisches Sortiersystem (Erweiterung zum Demonstrator)

Die zweite Arbeit transformiert das Erkennungssystem in einen geschlossenen mechatronischen Regelkreis. Es wurde ein fischertechnik-Förderband integriert, die Erkennung auf kontinuierlichen Bandbetrieb optimiert und ein webbasiertes Benutzer-Dashboard implementiert.

### Enthaltene Skripte & Funktionen:

* **`stepper.py`**
    * *Zweck:* Universelle Hardware-Abstraktionsklasse für die Sortierweiche.
    * *Funktion:* Steuert den Schrittmotor (Modell `28BYJ-48`) über die `ULN2003A`-Treiberplatine an. Die Klasse kapselt die präzise Ansteuerung der vier GPIO-Pins im Halbschrittmodus (8-Schritt-Sequenz), um die mechanische Sortierweiche materialschonend und exakt zu öffnen und zu schließen.
* **`Hauptsteuerprogramm_mit_webapp.py`**
    * *Zweck:* Das zentrale Nervensystem des mechatronischen Sortiersystems.
    * *Funktion:* Koordiniert das Gesamtsystem mithilfe von **Multithreading**, um Blockaden bei der Echtzeitanalyse zu verhindern.
        * *Thread 1 (Förderband & Vision):* Steuert den Bandmotor. Sobald eine Nudel die Lichtschranke passiert oder im Kamerafokus erfasst wird, wertet das optimierte YOLO-Modell den Frame aus. Handelt es sich um eine "beschädigte" Nudel, wird zeitverzögert (angepasst an die Bandgeschwindigkeit) die Klasse aus `stepper.py` aufgerufen, um die Weiche zu bewegen.
        * *Thread 2 (Webserver):* Startet die Flask-Webanwendung im Hintergrund, um Sensordaten und Systemzustände berührungslos bereitzustellen.
* **Web-Dashboard (`templates/` & `static/`)**
    * *Zweck:* Benutzeroberfläche zur Fernüberwachung und Steuerung des Systems.
    * *`templates/login.html` & `index.html`:* Bieten eine passwortgeschützte Weboberfläche. Das Dashboard zeigt einen Live-Videostream der Kamera inklusive der von YOLO eingezeichneten Erkennungsboxen.
    * *`static/js/app.js`:* Nutzt die **Fetch-API**, um die aktuellen Sortierzähler (Anzahl guter Nudeln vs. Ausschuss) im Hintergrund live vom Pi abzufragen und die HTML-Seite ohne Neuladen (asynchron) zu aktualisieren.
    * *`static/css/style.css`:* Definiert ein modernes, responsives Layout (CSS Grid/Flexbox), optimiert für die Steuerung über Smartphones und Tablets.

---

## 🛠️ Verwendete Schlüsseltechnologien
* **Inferenz-Engine:** Ultralytics YOLOv8 (für performante Ausführung via ONNX-Laufzeitumgebung auf dem RPi 5 exportiert).
* **Mechatronik & Sensorik:** GPIO-Ansteuerung via Python (`gpiozero`), Schrittmotor-Treiber, I2C-Bus-Kommunikation für Displays.
* **Webtech:** Flask (Python Webserver), HTML5, CSS3, JavaScript (Asynchroner Daten-Fetch).
