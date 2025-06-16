from flask import Flask, render_template, request, redirect, url_for
from config import Config
from models import db, Image
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from utils import get_image_features



app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Vérifie si un fichier a une extension correcte
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route principale : affichage + upload
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Vérifie qu’un fichier a été envoyé
        if 'image' not in request.files:
            return redirect(request.url)
        file = request.files['image']

        # Vérifie que le fichier n’est pas vide
        if file.filename == '':
            return redirect(request.url)
        
        # Vérifie que le fichier a une extension valide
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            #Extraction des features
            file_size, width, height, r_mean, g_mean, b_mean = get_image_features(filepath)

            # Crée une entrée dans la base de données
            new_img = Image(
             filename=filename,
             file_size=file_size,
             width=width,
             height=height,
             r_mean=r_mean,
             g_mean=g_mean,
             b_mean=b_mean
            )
            db.session.add(new_img)
            db.session.commit()
            return redirect(url_for('index'))

    images = Image.query.all()
    return render_template('index.html', images=images)

@app.route('/annotate/<int:image_id>/<string:label>')
def annotate(image_id, label):
    image = Image.query.get_or_404(image_id)
    image.annotation = label
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
