from PIL import Image as PILImage
import cv2
import numpy as np
import os
import json
import colorsys
from models import Rule


def get_image_features(image_path):
    # Taille fichier en Ko
    file_size = round(os.path.getsize(image_path) / 1024, 2)  # Ko

    # Ouvrir l'image avec PIL
    with PILImage.open(image_path) as img:
        width, height = img.size
        pixels = list(img.getdata())

        # Convertir en RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')
            pixels = list(img.getdata())

        # Moyennes R, G, B
        r_mean = round(sum(p[0] for p in pixels) / len(pixels), 2)
        g_mean = round(sum(p[1] for p in pixels) / len(pixels), 2)
        b_mean = round(sum(p[2] for p in pixels) / len(pixels), 2)

        # Contraste
        gray = img.convert('L')
        gray_pixels = np.array(gray.getdata())
        contrast = round(max(gray_pixels) - min(gray_pixels), 2)

        dark_pixels = np.sum(gray_pixels < 30)
        dark_pixel_ratio = round(dark_pixels / gray_pixels.size, 3)

        bright_pixels = np.sum(gray_pixels > 240)
        has_bright_spot = bool(bright_pixels > 0.01 * gray_pixels.size)

        # Edges avec OpenCV
        img_cv = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        edges_detected = False
        if img_cv is not None:
            edges = cv2.Canny(img_cv, 100, 200)
            edge_pixels = cv2.countNonZero(edges)
            total_pixels = img_cv.shape[0] * img_cv.shape[1]
            edges_detected = edge_pixels / total_pixels > 0.01

        # Histogramme compressé
        pixels_np = np.array(img.convert('RGB'))
        hist = []
        for i in range(3):
            channel_hist, _ = np.histogram(pixels_np[:, :, i], bins=16, range=(0, 256))
            hist.extend(channel_hist.tolist())
        histogram = json.dumps(hist)

        # Saturation moyenne
        pixels_np = np.array(img.convert('RGB')).reshape(-1, 3)
        saturations = []
        for r, g, b in pixels_np:
            h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            saturations.append(s)
        saturation_mean = round(np.mean(saturations), 3)

        # Analyse du bas de l'image (sol)
        img_np = np.array(gray)
        bottom_crop = img_np[-int(0.2 * height):, :]  # 20% inférieurs
        bright_bottom = np.sum(bottom_crop > 180)
        total_bottom = bottom_crop.size
        bright_ratio_bottom = round(bright_bottom / total_bottom, 3)

    return (
        file_size, width, height,
        r_mean, g_mean, b_mean,
        contrast, edges_detected,
        histogram, saturation_mean,
        dark_pixel_ratio, has_bright_spot,
        bright_ratio_bottom
    )


def auto_classify_score(
    r_mean, g_mean, b_mean, contrast,
    dark_pixel_ratio, has_bright_spot,
    saturation_mean, file_size, width, height,
    edges_detected, bright_ratio_bottom
):
    """
    Calcule un score de remplissage de poubelle entre 0 et 1.
    Plus c'est proche de 1, plus la poubelle est probablement pleine.
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

    # Règle 5 : reflet + image claire = vide probable
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

    # Règle 9 : contours nets → potentiels objets = déchets visibles
    if edges_detected:
        score += 1 * 0.1
    else:
        score += 0.3 * 0.1
    total_weight += 0.1

    # Règle 10 : clair en bas de l’image = sacs au sol = poubelle débordante
    if bright_ratio_bottom > 0.2:
        score += 1 * 0.3
    else:
        score += 0 * 0.3
    total_weight += 0.3

    # Score final normalisé
    final_score = round(score / total_weight, 3)
    return final_score


def auto_classify_by_score(*args, threshold=0.6):
    score = auto_classify_score(*args)
    return "pleine" if score >= threshold else "vide"

def classify_dynamic(features_dict, session):
    """
    Applique les règles stockées en base pour déterminer une classification.
    - features_dict : dictionnaire {nom_feature: valeur}
    - session : db.session (à passer depuis Flask)
    """
    rules = session.query(Rule).all()

    for rule in rules:
        value = features_dict.get(rule.feature)
        if value is None:
            continue

        expression = f"{value} {rule.operator} {rule.threshold}"
        try:
            if eval(expression):
                return rule.label  # première règle satisfaite = classification appliquée
        except Exception as e:
            print(f"Erreur évaluation règle : {expression} – {e}")

    return "non défini"

def get_exif_gps(image_path):
    """
    Extrait la latitude et la longitude GPS depuis les métadonnées EXIF d'une image (si présentes).
    Retourne (latitude, longitude) ou (None, None) si absent.
    """
    try:
        with PILImage.open(image_path) as img:
            exif = img._getexif()
            if not exif:
                return None, None
            from PIL.ExifTags import TAGS, GPSTAGS
            gps_info = None
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_info = value
                    break
            if not gps_info:
                return None, None
            def _convert_to_degrees(value):
                d, m, s = value
                return float(d[0]) / float(d[1]) + float(m[0]) / float(m[1]) / 60 + float(s[0]) / float(s[1]) / 3600
            lat = lon = None
            gps_latitude = gps_info.get(2)
            gps_latitude_ref = gps_info.get(1)
            gps_longitude = gps_info.get(4)
            gps_longitude_ref = gps_info.get(3)
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = _convert_to_degrees(gps_latitude)
                if gps_latitude_ref != 'N':
                    lat = -lat
                lon = _convert_to_degrees(gps_longitude)
                if gps_longitude_ref != 'E':
                    lon = -lon
                return lat, lon
    except Exception as e:
        print(f"Erreur extraction EXIF GPS : {e}")
    return None, None

def compress_and_convert_webp(image_path, quality=80):
    """
    Convertit une image en WebP compressé et retourne le chemin du nouveau fichier.
    """
    import os
    webp_path = os.path.splitext(image_path)[0] + '.webp'
    with PILImage.open(image_path) as img:
        img = img.convert('RGB')
        img.save(webp_path, 'webp', quality=quality, method=6)
    return webp_path