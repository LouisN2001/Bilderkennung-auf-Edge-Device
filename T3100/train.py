from ultralytics import YOLO
import torch
import os


if __name__ == '__main__':
    # Basis-Pfade
    BASE_PATH = "C:/xxx/YOLO_Programmierung/Programmierung_Python"
    DATA_PATH = os.path.join(BASE_PATH, "data").replace("\\", "/")
    CONFIG_PATH = os.path.join(BASE_PATH, "config.yaml").replace("\\", "/")
    TRAIN_FOLDER = os.path.join(DATA_PATH, "images/train").replace("\\", "/")


    PROJECT_NAME = "YOLOv8-Fliesband"
    EXPERIMENT_NAME = "Test1-Fliessband"


    # Reslut-File (im Experimente-Ordner)
    EXPERIMENT_DIR = os.path.join(
        BASE_PATH,
        PROJECT_NAME,
        EXPERIMENT_NAME
    ).replace("\\", "/")

    RESULTS_FILE = os.path.join(
        EXPERIMENT_DIR,
        "test_results.txt"
    ).replace("\\", "/")

    os.makedirs(EXPERIMENT_DIR, exist_ok=True)

    #  Prüfen, ob config.yaml existiert
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Die config.yaml existiert nicht unter {CONFIG_PATH}")

    #  Training auf GPU
    if torch.cuda.is_available():
        device = 'cuda:0'
        print("CUDA GPU erkannt, Training auf GPU.")
    else:
        device = 'cpu'
        print("Keine GPU erkannt, Training auf CPU.")

    # YOLOv8 Modell
    model = YOLO("yolov8n.yaml")

    #  Trainings-Parameter
    model.train(
        data="config.yaml",
        project=os.path.join(BASE_PATH, PROJECT_NAME),
        name=EXPERIMENT_NAME,
        exist_ok=True,
        epochs=300,
        imgsz=320,
        batch=16,
        device=device,
        augment=True,
        patience=30,  # Early Stopping
    )

    # Test-Set Evaluation
    results_test = model.val(split="test")

    # Test Ergebnisse in Textdatei schreiben
    os.makedirs(TRAIN_FOLDER, exist_ok=True)  # Sicherstellen, dass Train-Ordner existiert

    # Test-Ergebnisse schreiben (bestes Modell)
    precision, recall, mAP50, mAP50_95 = results_test.mean_results()

    with open(RESULTS_FILE, "w") as f:
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall: {recall:.4f}\n")
        f.write(f"mAP50: {mAP50:.4f}\n")
        f.write(f"mAP50-95: {mAP50_95:.4f}\n")

        class_maps = results_test.maps  # numpy array

        for i, ap in enumerate(class_maps):
            print(f"Class {i} AP: {ap:.4f}")

    print(f"Test results saved to: {RESULTS_FILE}")

    # ONNX-Export (bestes Modell)
    weights_dir = os.path.join(
        BASE_PATH,
        PROJECT_NAME,
        EXPERIMENT_NAME,
        "weights"
    ).replace("\\", "/")

    best_model_path = os.path.join(weights_dir, "best.pt").replace("\\", "/")

    if not os.path.exists(best_model_path):
        raise FileNotFoundError(f"best.pt nicht gefunden: {best_model_path}")

    print("Exportiere best.pt nach ONNX...")

    best_model = YOLO(best_model_path)
    best_model.export(
        format="onnx",
        imgsz=640,
        opset=12,
        simplify=True
    )

    print("ONNX Export abgeschlossen.")
    print(f"ONNX-Datei liegt in: {weights_dir}")
