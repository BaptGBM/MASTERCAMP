import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
import os

# ✅ Paramètres
IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 10
DATASET_DIR = "dataset_cnn"

# ✅ Prétraitement des données
train_datagen = ImageDataGenerator(rescale=1./255)
val_datagen = ImageDataGenerator(rescale=1./255)

train_gen = train_datagen.flow_from_directory(
    os.path.join(DATASET_DIR, "train"),
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary'
)

val_gen = val_datagen.flow_from_directory(
    os.path.join(DATASET_DIR, "val"),
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary'
)

# ✅ Modèle CNN avec MobileNetV2
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(128, 128, 3))
base_model.trainable = False

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(64, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# ✅ Entraînement
history = model.fit(train_gen, epochs=EPOCHS, validation_data=val_gen)

# Évaluer les performances du modèle sur le jeu de validation
val_loss, val_accuracy = model.evaluate(val_gen)
print(f"\n✅ Accuracy sur la validation : {val_accuracy:.4f} | Loss : {val_loss:.4f}")

# Récupération des vraies classes et prédictions
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

y_true = val_gen.classes
y_pred_probs = model.predict(val_gen)
y_pred = np.argmax(y_pred_probs, axis=1)

# Affichage du rapport de classification
print("\n📊 Rapport de classification :")
print(classification_report(y_true, y_pred, target_names=val_gen.class_indices.keys()))

# Matrice de confusion
print("🧩 Matrice de confusion :")
print(confusion_matrix(y_true, y_pred))


# ✅ Sauvegarde
model.save("model_pleine_vide.h5")
print("✅ Modèle sauvegardé sous model_pleine_vide.h5")
