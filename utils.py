from PIL import Image as PILImage
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

    return file_size, width, height, r_mean, g_mean, b_mean
