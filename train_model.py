import pandas as pd
from models import Image

def get_labeled_data(session):
    images = session.query(Image).filter(Image.annotation.in_(["pleine", "vide"])).all()
    data = [{
        'r_mean': img.r_mean,
        'g_mean': img.g_mean,
        'b_mean': img.b_mean,
        'contrast': img.contrast,
        'saturation_mean': img.saturation_mean,
        'dark_pixel_ratio': img.dark_pixel_ratio,
        'has_bright_spot': img.has_bright_spot,
        'label': 1 if img.annotation == "pleine" else 0
    } for img in images]
    return pd.DataFrame(data)


from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

df = get_labeled_data(session)

X = df.drop("label", axis=1)
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test)))
joblib.dump(model, "ml_model.pkl")

import joblib

ML_MODEL = joblib.load("ml_model.pkl")

def classify_ml(features_dict):
    X = [[
        features_dict["r_mean"],
        features_dict["g_mean"],
        features_dict["b_mean"],
        features_dict["contrast"],
        features_dict["saturation_mean"],
        features_dict["dark_pixel_ratio"],
        int(features_dict["has_bright_spot"])
    ]]
    pred = ML_MODEL.predict(X)[0]
    return "pleine" if pred == 1 else "vide"
