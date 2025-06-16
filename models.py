from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
