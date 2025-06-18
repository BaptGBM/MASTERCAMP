from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialise l'objet SQLAlchemy, utilisé pour manipuler la base de données
db = SQLAlchemy()

# Définition du modèle Image → correspond à une table dans la base de données
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), unique=True, nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)
    annotation = db.Column(db.String(10))  # 'pleine' ou 'vide'
    file_size = db.Column(db.Float)  # en Ko
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    r_mean = db.Column(db.Float)
    g_mean = db.Column(db.Float)
    b_mean = db.Column(db.Float)
    contrast = db.Column(db.Float)
    edges = db.Column(db.Boolean)
    histogram = db.Column(db.String)  # Stocké en JSON
    saturation_mean = db.Column(db.Float)
