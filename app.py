from flask import Flask, render_template, request, redirect, url_for
from config import Config
from models import db, Image, Rule
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from utils import get_image_features, auto_classify_score, classify_dynamic
import uuid

# Initialisation de l’application Flask
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'image' not in request.files:
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            file_size, width, height, r_mean, g_mean, b_mean, contrast, edges_detected, histogram, saturation_mean, dark_pixel_ratio, has_bright_spot = get_image_features(filepath)

            score = auto_classify_score(
                r_mean, g_mean, b_mean, contrast,
                dark_pixel_ratio, has_bright_spot,
                saturation_mean, file_size, width, height 
            )

            features_dict = {
                "r_mean": r_mean,
                "g_mean": g_mean,
                "b_mean": b_mean,
                "contrast": contrast,
                "dark_pixel_ratio": dark_pixel_ratio,
                "has_bright_spot": has_bright_spot,
                "saturation_mean": saturation_mean,
                "file_size": file_size,
                "width": width,
                "height": height
            }

            annotation_auto = classify_dynamic(features_dict, db.session)

            if annotation_auto == "non défini":
                annotation_auto = "pleine" if score >= 0.6 else "vide"

            new_img = Image(
                filename=filename,
                file_size=file_size,
                width=width,
                height=height,
                r_mean=r_mean,
                g_mean=g_mean,
                b_mean=b_mean,
                contrast=contrast,
                edges=edges_detected,
                histogram=histogram,
                saturation_mean=saturation_mean,
                dark_pixel_ratio=dark_pixel_ratio,
                has_bright_spot=has_bright_spot,
                annotation=annotation_auto,
                score=score
            )
            db.session.add(new_img)
            db.session.commit()
            return redirect(url_for('index'))

    images = Image.query.order_by(Image.id.desc()).all()
    last_image = images[0] if images else None
    return render_template('index.html', images=images, last_image=last_image)

@app.route('/annotate/<int:image_id>/<string:label>')
def annotate(image_id, label):
    image = Image.query.get_or_404(image_id)
    image.annotation = label
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        feature = request.form['feature']
        operator = request.form['operator']
        threshold = float(request.form['threshold'])
        label = request.form['label']
        confidence = int(request.form['confidence'])

        new_rule = Rule(
            feature=feature,
            operator=operator,
            threshold=threshold,
            label=label,
            confidence=confidence
        )
        db.session.add(new_rule)
        db.session.commit()
        return redirect(url_for('config'))

    rules = Rule.query.all()
    return render_template('config.html', rules=rules)

# ✅ Ce bloc doit être **à la toute fin**
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
