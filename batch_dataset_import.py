import os
import uuid
import shutil
from app import app, db
from models import Image
from utils import get_image_features, auto_classify_score, classify_dynamic
from datetime import datetime

BASE_FOLDER = "dataset/Data"  # corriger ici selon ta structure
DEST_FOLDER = app.config["UPLOAD_FOLDER"]
os.makedirs(DEST_FOLDER, exist_ok=True)

def process_image(img_path, annotation=None):
    ext = img_path.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(DEST_FOLDER, filename)
    shutil.copy(img_path, dest_path)

    features = get_image_features(dest_path)
    file_size, width, height, r_mean, g_mean, b_mean, contrast, edges, histogram, saturation, dark_ratio, bright = features

    score = auto_classify_score(r_mean, g_mean, b_mean, contrast, dark_ratio, bright, saturation, file_size, width, height)

    if annotation is None:
        features_dict = {
            "r_mean": r_mean, "g_mean": g_mean, "b_mean": b_mean,
            "contrast": contrast, "dark_pixel_ratio": dark_ratio,
            "has_bright_spot": bright, "saturation_mean": saturation,
            "file_size": file_size, "width": width, "height": height
        }
        annotation = classify_dynamic(features_dict, db.session)
        if annotation == "non défini":
            annotation = "pleine" if score >= 0.6 else "vide"

    image = Image(
        filename=filename,
        file_size=file_size,
        width=width,
        height=height,
        r_mean=r_mean,
        g_mean=g_mean,
        b_mean=b_mean,
        contrast=contrast,
        edges=edges,
        histogram=histogram,
        saturation_mean=saturation,
        dark_pixel_ratio=dark_ratio,
        has_bright_spot=bright,
        annotation=annotation,
        score=score,
        date_uploaded=datetime.utcnow()
    )
    db.session.add(image)
    print(f"✓ {filename} → {annotation}")

def import_all_images():
    with app.app_context():
        # labeled/dirty => pleine
        labeled_dirty = os.path.join(BASE_FOLDER, "train", "with_label", "dirty")
        for fname in os.listdir(labeled_dirty):
            process_image(os.path.join(labeled_dirty, fname), annotation="pleine")

        # labeled/clean => vide
        labeled_clean = os.path.join(BASE_FOLDER, "train", "with_label", "clean")
        for fname in os.listdir(labeled_clean):
            process_image(os.path.join(labeled_clean, fname), annotation="vide")

        # nolabeled => IA
        no_label_folder = os.path.join(BASE_FOLDER, "train", "no_label")
        for subdir in os.listdir(no_label_folder):
            subpath = os.path.join(no_label_folder, subdir)
            for fname in os.listdir(subpath):
                process_image(os.path.join(subpath, fname))

        # test/images => IA
        test_folder = os.path.join(BASE_FOLDER, "test")
        for fname in os.listdir(test_folder):
            process_image(os.path.join(test_folder, fname))

        db.session.commit()
        print("✅ Import terminé avec succès !")

if __name__ == "__main__":
    import_all_images()
