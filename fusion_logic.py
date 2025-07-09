def fusion_cnn_yolo(cnn_pred, yolo_classes):
    """
    Combine la prédiction CNN + objets détectés par YOLO
    """
    if cnn_pred == "vide" and any(obj in yolo_classes for obj in ["bag", "bottle", "box"]):
        return "pleine"
    return cnn_pred