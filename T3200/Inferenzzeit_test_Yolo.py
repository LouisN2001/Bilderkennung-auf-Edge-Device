from ultralytics import YOLO
import os
import glob

MODEL_PATH = "C:/Users/cnorm/OneDrive/Dokumente/YOLO_Programmierung/Programmierung_Python/YOLOv8-Fliesband/Test1-Fliessband/weights/best.onnx"
IMAGE_DIR = "C:/Users/cnorm/OneDrive/Dokumente/YOLO_Programmierung/Inferenzzeit_test"

# YOLO-Modell Laden
model = YOLO(MODEL_PATH, task='detect')

# Bilder laden
image_paths = []
for ext in ["*.jpg", "*.jpeg", "*.png"]:
    image_paths.extend(glob.glob(os.path.join(IMAGE_DIR, ext)))
image_paths = sorted(image_paths)[:100]

if not image_paths:
    print("Keine Bilder gefunden.")
    exit()

inference_times = []

print(f"Starte Analyse von {len(image_paths)} Bildern...\n")

for i, image_path in enumerate(image_paths, start=1):
    results = model.predict(
        source=image_path,
        conf=0.5,
        save=False,
        verbose=False
    )

    # Zeit extrahieren
    inference_time = results[0].speed["inference"]

    # Wert zur Liste hinzufügen
    inference_times.append(inference_time)

    print(f"Bild {i}: {os.path.basename(image_path)}")
    print(f"Inferenzzeit: {inference_time:.2f} ms | FPS: {1000 / inference_time:.2f}")
    print("-" * 30)

# Durchschnitt berechnen
if inference_times:

    # Bild 1 ignorieren, da dies immer länger braucht als durchschnittlich: 106ms im gegensatz zu 14ms gesamt
    adjusted_times = inference_times[1:] if len(inference_times) > 1 else inference_times

    avg_inference = sum(adjusted_times) / len(adjusted_times)
    avg_fps = 1000 / avg_inference

    print("\nERGEBNIS (ohne Warmup-Bild):")
    print(f"Durchschnittliche Inferenzzeit: {avg_inference:.2f} ms")
    print(f"Durchschnittliche FPS: {avg_fps:.2f}")