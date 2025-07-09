from ultralytics import YOLO
import cv2

# Charge le modèle pré-entraîné (yolov8n = rapide, yolov8m = plus précis)
model = YOLO('yolov8n.pt')  # ou 'yolov8m.pt'

# Liste des classes importantes à détecter (tu peux ajuster)
CIBLES = ["bottle", "bag", "backpack", "box"]

def detect_objects_yolo(image_path):
    results = model(image_path)[0]  # résultat pour une seule image

    detected_classes = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        detected_classes.append(cls_name)

    # On garde uniquement les classes utiles (filtrées)
    filtered = [cls for cls in detected_classes if cls in CIBLES]
    return filtered
