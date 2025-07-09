from predict_cnn import predict_cnn
from predict_yolo import detect_objects_yolo
from fusion_logic import fusion_cnn_yolo

def predict_final(image_path):
    cnn_pred = predict_cnn(image_path)
    yolo_objs = detect_objects_yolo(image_path)
    final = fusion_cnn_yolo(cnn_pred, yolo_objs)
    return final
