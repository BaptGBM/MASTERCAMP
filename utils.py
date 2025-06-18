from PIL import Image as PILImage
import cv2
import numpy as np
import os


def get_image_features(image_path):
    # Taille fichier en Ko
    file_size = round(os.path.getsize(image_path) / 1024, 2)  # Ko

    # Ouvrir l’image avec PIL
    with PILImage.open(image_path) as img:
        width, height = img.size
        pixels = list(img.getdata())

        # Convertir en RGB si l’image est en mode L ou autre
        if img.mode != 'RGB':
            img = img.convert('RGB')
            pixels = list(img.getdata())

        # Moyennes R, G, B
        r_total = sum(p[0] for p in pixels)
        g_total = sum(p[1] for p in pixels)
        b_total = sum(p[2] for p in pixels)
        count = len(pixels)

        r_mean = round(r_total / count, 2)
        g_mean = round(g_total / count, 2)
        b_mean = round(b_total / count, 2)

         # Contraste : différence entre le pixel le plus sombre et le plus clair (en niveaux de gris)
        gray = img.convert('L')
        gray_pixels = list(gray.getdata())
        contrast = round(max(gray_pixels) - min(gray_pixels), 2)

         # Ouvrir avec OpenCV pour la détection de contours
        img_cv = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        edges_detected = False
        if img_cv is not None:
             edges = cv2.Canny(img_cv, 100, 200)
             edge_pixels = cv2.countNonZero(edges)
             total_pixels = img_cv.shape[0] * img_cv.shape[1]
             edges_detected = edge_pixels / total_pixels > 0.01  # seuil arbitraire de 1%


    return file_size, width, height, r_mean, g_mean, b_mean , contrast, edges_detected


