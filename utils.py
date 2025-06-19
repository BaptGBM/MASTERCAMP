from PIL import Image as PILImage
import cv2
import numpy as np
import os
import json
import colorsys

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
        gray_pixels = np.array(gray.getdata())
        dark_pixels = np.sum(gray_pixels < 30)  # Seuil de pixel sombre
        dark_pixel_ratio = round(dark_pixels / gray_pixels.size, 3)
        bright_pixels = np.sum(gray_pixels > 240)
        has_bright_spot = bool(bright_pixels > 0.01 * gray_pixels.size)


        contrast = round(max(gray_pixels) - min(gray_pixels), 2)

         # Ouvrir avec OpenCV pour la détection de contours
        img_cv = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        edges_detected = False
        if img_cv is not None:
             edges = cv2.Canny(img_cv, 100, 200)
             edge_pixels = cv2.countNonZero(edges)
             total_pixels = img_cv.shape[0] * img_cv.shape[1]
             edges_detected = edge_pixels / total_pixels > 0.01  # seuil arbitraire de 1%
        
        # Histogramme compressé (16 classes pour R, G, B)
        pixels_np = np.array(img.convert('RGB'))
        hist = []
        for i in range(3):  # R, G, B
            channel_hist, _ = np.histogram(pixels_np[:, :, i], bins=16, range=(0, 256))
            hist.extend(channel_hist.tolist())
        histogram = json.dumps(hist)  # Pour stocker dans la BDD

        # Convertir les pixels en tableau NumPy
        pixels_np = np.array(img.convert('RGB')).reshape(-1, 3)

        # Calcul de la saturation pour chaque pixel
        saturations = []
        for r, g, b in pixels_np:
              r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
              h, l, s = colorsys.rgb_to_hls(r_, g_, b_)
              saturations.append(s)

        saturation_mean = round(np.mean(saturations), 3)


    return file_size, width, height, r_mean, g_mean, b_mean , contrast, edges_detected , histogram , saturation_mean , dark_pixel_ratio , has_bright_spot

def auto_classify_score(r_mean, g_mean, b_mean, contrast, dark_pixel_ratio, has_bright_spot, saturation_mean, file_size, width, height):
    """
    Calcule un score de remplissage de poubelle entre 0 et 1.
    Plus c’est proche de 1, plus la poubelle est probablement pleine.
    """

    score = 0
    total_weight = 0

    # Règle 1 : image sombre = poubelle pleine
    if dark_pixel_ratio > 0.3:
        score += 1 * 0.25
    total_weight += 0.25

    # Règle 2 : faible contraste → vide probable
    if contrast < 50:
        score += 0.3 * 0.1
    else:
        score += 1 * 0.1
    total_weight += 0.1

    # Règle 3 : couleurs très claires = vide
    if r_mean > 180 and g_mean > 180 and b_mean > 180:
        score += 0 * 0.1
    else:
        score += 1 * 0.1
    total_weight += 0.1

    # Règle 4 : saturation élevée = sacs colorés = pleine
    if saturation_mean > 0.6:
        score += 1 * 0.1
    total_weight += 0.1

    # Règle 5 : reflet + image claire = vide
    if has_bright_spot and r_mean > 150:
        score += 0 * 0.1
    else:
        score += 1 * 0.1
    total_weight += 0.1

    # Règle 6 : fichier très léger (< 100 Ko) = doute
    if file_size < 100:
        score += 0.3 * 0.1
    else:
        score += 1 * 0.1
    total_weight += 0.1

    # Règle 7 : image très petite = doute
    image_size = width * height
    if image_size < 200000:  # par exemple : 400x500
        score += 0.2 * 0.05
    else:
        score += 1 * 0.05
    total_weight += 0.05

    # Règle 8 : couleurs déséquilibrées = sacs visibles
    if abs(r_mean - g_mean) > 20 or abs(g_mean - b_mean) > 20:
        score += 1 * 0.1
    total_weight += 0.1

    # Score final normalisé
    final_score = round(score / total_weight, 3)
    return final_score


def auto_classify_by_score(*args, threshold=0.6):
    score = auto_classify_score(*args)
    return "pleine" if score >= threshold else "vide"

