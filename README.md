# Edge-Computing-System zur Echtzeit-Objekterkennung und Sortierung von Nudeln

Dieses Repository enthält die vollständige Codebasis für die zwei aufeinander aufbauenden Studienarbeiten (Module T3100 und T3200) im Studiengang Mechatronik an der DHBW Stuttgart. 

Das Gesamtziel des Projekts war die Entwicklung eines kostengünstigen, lokalen Edge-AI-Systems auf Basis eines ausgewählten Edge-Systems (wir haben uns für den Raspberry Pi 5 entschieden), das verschiedene Nudelsorten sowie beschädigte Nudeln in Echtzeit klassifiziert und über ein automatisiertes Förderband physisch aussortiert.



## T3100: Bilderkennung mit Edge-Device (Grundlagen & KI-Training)

Die erste Arbeit konzentrierte sich auf den Aufbau des Edge-Devices, die Datengenerierung sowie das Training und die lokale Implementierung des Objekterkennungsmodells YOLOv8. Die Auslösung der Kamera und die Ausgabe der Erkennungsergebnisse erfolgten hier noch rein hardwarebasiert über Taster und OLED-Display.

### Enthaltene Skripte & Funktionen:

* **`Bilder_Aufnehmen.py`**
    * Zweck: Automatisierte Datenerfassung für den Bilddatensatz.
    * Funktion: Steuert das Raspberry Pi Kamera Modul 3 an, führt vor jeder Aufnahme einen Autofokus-Zyklus (`autofocus_cycle()`) durch und speichert die Bilder mit einem fortlaufenden Index ab.
* **`Splitting_dataset.py`**
    * Zweck: Strukturierung des Datensatzes vor dem Training.
    * Funktion: Teilt die annotierten Bilddaten in ein Verhältnis von 70% Training, 20% Validierung und 10% Testdaten auf. Es erstellt automatisch die von YOLO geforderte Ordnerstruktur und verschiebt die Bild- und Textdateien (`.txt` mit Bounding-Box-Koordinaten) entsprechend.
* **`train.py`**
    * Zweck: Training des YOLO-Modells.
    * Funktion: Startet das Training des `yolov8n.pt`-Modells. Es nutzt die Konfiguration aus der `config.yaml`, um das Modell auf die spezifischen Nudelklassen (z. B. intakte/beschädigte Nudeln) über eine variable Anzahl an Epochen hinweg zu trainieren.
* **`config.yaml`**
    * Zweck: Datensatz-Konfiguration für das YOLO-Framework.
    * Funktion: Definiert für den Trainingsalgorithmus die absoluten oder relativen Pfade zu den Trainings-, Validierungs- und Testbildern. Zudem enthält sie die exakte Anzahl der Klassen sowie deren namentliche Zuordnung (z. B. intakte Nudeln, beschädigte Nudeln).
* **`bild_detector.py`**
    * Zweck: Lokales Hauptprogramm der ersten Projektphase, das auf dem Raspberry Pi läuft.
    * Funktion: Läuft in einer Endlosschleife und wartet auf ein Hardwaresignal via `gpiozero` (Knopfdruck an Pin 17). Nach dem Auslösen wird ein Bild aufgenommen, die lokale KI-Inferenz gestartet und das Ergebnis (Anzahl & Typ der Nudeln) formatiert auf dem per I2C angebundenen OLED-Display ausgegeben.



## T3200: Mechatronisches Sortiersystem (Erweiterung zum Demonstrator)

Die zweite Arbeit entwickelt das Erkennungssystem weiter. Es wurde ein fischertechnik-Förderband integriert, die Erkennung auf kontinuierlichen Bandbetrieb optimiert und ein webbasiertes Benutzer-Dashboard implementiert.

### Enthaltene Skripte & Funktionen:

* **`Hauptsteuerprogramm_mit_webapp.py`**
    * Zweck: Das zentrale Hauptsteuerprogramm des mechatronischen Sortiersystems, das auf dem Raspberry Pi 5 läuft.
    * Funktion: Koordiniert das Gesamtsystem parallel mithilfe von Multithreading, um Blockaden bei der Echtzeitanalyse zu verhindern. Ein Thread steuert den kontinuierlichen Bandbetrieb. Ein zweiter Thread wertet Kamerabilder bei Objekterkennung aus und steuert zeitverzögert die Aussortierung. Der dritte Thread Thread hostet parallel den Flask-Webserver für das Live-Dashboard.
* **`Stepper.py`**
    * Zweck: Universelle Hardware-Abstraktionsklasse für die Sortierweiche.
    * Funktion: Kapselt die  GPIO-Ansteuerung des Schrittmotors (Modell `28BYJ-48`) über die `ULN2003A`-Treiberplatine. Die Klasse realisiert eine verschleißarme 8-Schritt-Sequenz im Halbschrittmodus, um die mechanische Sortierweiche materialschonend und exakt zu öffnen und zu schließen.
* **`login.html`** *(in Ordner templates/)*
    * Zweck: Authentifizierungskomponente der Benutzeroberfläche.
    * Funktion: Stellt eine einfache, optisch ansprechende Login-Maske für die Flask-Webapp bereit, um das mechatronische System vor unbefugten Zugriffen zu schützen.
* **`manifest.json`** *(in Ordner static/)*
    * Zweck: Bereitstellung als  Web App .
    * Funktion: Enthält Metadaten (Symbole, Start-URL, App-Namen), die es ermöglichen, das Web-Dashboard wie eine native App direkt auf dem Startbildschirm von Smartphones oder Tablets zu installieren.
* **`index.html`** *(in Ordner templates/)*
    * Zweck: Hauptbedienoberfläche des Sortiersystems.
    * Funktion: Visualisiert das interaktive Steuerungs-Dashboard. Es bindet den Live-Videostream der Raspberry Pi Kamera (inklusive der von YOLO generierten Erkennungsboxen) ein und zeigt Echtzeit-Statistiken über die Sortierzähler.
* **`Inferenzzeit_test_Yolo.py`**
    * Zweck: Performance-Analyse und Validierung.
    * Funktion: Ein automatisiertes Testskript, das die Inferenzzeiten des trainierten YOLO-Modells über eine Testreihe von 100 Bildern misst. Es berechnet die durchschnittliche Verarbeitungszeit in Millisekunden sowie die resultierenden Frames per Second (FPS), um die Echtzeitfähigkeit auf dem Edge-Device mathematisch nachzuweisen.

---


##  Quellen

* **Schrittmotor-Ansteuerung (`stepper.py`):** Die grundlegende Logik zur Ansteuerung des Schrittmotors über die ULN2003A-Treiberplatine basiert auf dem Open-Source-Repository [stepper](https://github.com/alecxcode/stepper) von alecxcode. Der Code wurde unter den Bedingungen der MIT-Lizenz wiederverwendet.
