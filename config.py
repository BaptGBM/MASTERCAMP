import os

basedir = os.path.abspath(os.path.dirname(__file__)) # Chemin absolu du répertoire de base


class Config:
   SQLALCHEMY_DATABASE_URI = "postgresql://postgres:ySZCvNQtaYMOwErbMrnTIJPpNtrpxNbj@yamanote.proxy.rlwy.net:10386/railway"
   SQLALCHEMY_TRACK_MODIFICATIONS = False
   UPLOAD_FOLDER = "static/uploads"
