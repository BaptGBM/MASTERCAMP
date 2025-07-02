from flask import Flask, render_template, request, redirect, url_for
from config import Config
from models import db, Image, Rule
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from utils import get_image_features, auto_classify_score, classify_dynamic
import uuid
import csv
from flask import Response, jsonify




# Initialisation de l'application Flask
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
            # Récupère l'annotation manuelle si fournie
            manual_annotation = request.form.get('annotation_manual')

            # Récupération de la localisation si fournie
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')

            # Enregistre l'image localement
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Si pas de localisation fournie, tente d'extraire depuis EXIF
            if not latitude or not longitude:
                from utils import get_exif_gps
                lat_exif, lon_exif = get_exif_gps(filepath)
                if lat_exif is not None and lon_exif is not None:
                    latitude = lat_exif
                    longitude = lon_exif

            # Extraction des features
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

            # IA dynamique avec règles
            annotation_auto = classify_dynamic(features_dict, db.session)

            # Résultat final
            if manual_annotation in ['pleine', 'vide']:
                annotation_finale = manual_annotation
            else:
                annotation_finale = annotation_auto if annotation_auto != "non défini" else ("pleine" if score >= 0.6 else "vide")

            # Enregistrement en base
            new_img = Image(
                filename=filename,
                file_size=float(file_size),
                width=int(width),
                height=int(height),
                r_mean=float(r_mean),
                g_mean=float(g_mean),
                b_mean=float(b_mean),
                contrast=int(contrast),
                edges=bool(edges_detected),
                histogram=str(histogram),  # important ! JSON ou string, pas d'objet numpy
                saturation_mean=float(saturation_mean),
                dark_pixel_ratio=float(dark_pixel_ratio),
                has_bright_spot=bool(has_bright_spot),
                annotation=annotation_finale,
                score=float(score),
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None
            )

            db.session.add(new_img)
            db.session.commit()
            return redirect(url_for('index'))

    images = Image.query.order_by(Image.id.desc()).all()
    last_image = images[0] if images else None
    # Préparer la dernière localisation connue pour le template
    last_lat = last_image.latitude if last_image and last_image.latitude else None
    last_lon = last_image.longitude if last_image and last_image.longitude else None
    return render_template('index.html', images=images, last_image=last_image, last_lat=last_lat, last_lon=last_lon)


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

@app.route('/export/csv')
def export_csv():
    images = Image.query.all()

    def generate():
        yield 'ID,Filename,Date,Annotation,Score,Taille,Width,Height,R,G,B,Contrast,Saturation,DarkPixels,BrightSpot\n'
        for img in images:
            yield f"{img.id},{img.filename},{img.date_uploaded},{img.annotation or ''},{img.score or ''}," \
                  f"{img.file_size},{img.width},{img.height},{img.r_mean},{img.g_mean},{img.b_mean}," \
                  f"{img.contrast},{img.saturation_mean},{img.dark_pixel_ratio},{img.has_bright_spot}\n"

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=ecotrash_data.csv"})

@app.route('/api/images')
def api_images():
    images = Image.query.order_by(Image.id.desc()).all()
    data = []
    for img in images:
        data.append({
            "id": img.id,
            "filename": img.filename,
            "date_uploaded": img.date_uploaded.isoformat(),
            "annotation": img.annotation,
            "score": img.score,
            "file_size": img.file_size,
            "width": img.width,
            "height": img.height,
            "r_mean": img.r_mean,
            "g_mean": img.g_mean,
            "b_mean": img.b_mean,
            "contrast": img.contrast,
            "saturation_mean": img.saturation_mean,
            "dark_pixel_ratio": img.dark_pixel_ratio,
            "has_bright_spot": img.has_bright_spot,
        })
    return jsonify(data)

@app.route('/api/latest')
def api_latest_image():
    latest = Image.query.order_by(Image.id.desc()).first()
    if not latest:
        return jsonify({"error": "Aucune image trouvée"}), 404

    return jsonify({
        "id": latest.id,
        "filename": latest.filename,
        "date_uploaded": latest.date_uploaded,
        "annotation": latest.annotation,
        "score": latest.score,
        "file_size": latest.file_size,
        "width": latest.width,
        "height": latest.height,
        "r_mean": latest.r_mean,
        "g_mean": latest.g_mean,
        "b_mean": latest.b_mean,
        "contrast": latest.contrast,
        "saturation_mean": latest.saturation_mean,
        "dark_pixel_ratio": latest.dark_pixel_ratio,
        "has_bright_spot": latest.has_bright_spot
    })

@app.route('/api/image/<int:image_id>', methods=['PUT'])
def api_update_annotation(image_id):
    image = Image.query.get_or_404(image_id)
    data = request.get_json()

    if 'annotation' not in data:
        return jsonify({"error": "Champ 'annotation' requis"}), 400

    image.annotation = data['annotation']
    db.session.commit()

    return jsonify({"message": f"Image {image_id} mise à jour avec succès."})

@app.route('/api/stats')
def api_stats():
    images = Image.query.all()
    total = len(images)
    pleines = [img for img in images if img.annotation == "pleine"]
    vides = [img for img in images if img.annotation == "vide"]

    moyenne_score = round(sum(img.score for img in images if img.score is not None) / total, 3) if total else 0
    moyenne_pleines = round(sum(img.score for img in pleines if img.score is not None) / len(pleines), 3) if pleines else 0
    moyenne_vides = round(sum(img.score for img in vides if img.score is not None) / len(vides), 3) if vides else 0

    return jsonify({
        "total_images": total,
        "pleines": len(pleines),
        "vides": len(vides),
        "score_moyen": moyenne_score,
        "score_moyen_pleines": moyenne_pleines,
        "score_moyen_vides": moyenne_vides
    })


@app.route('/api/images')
def api_filter_images():
    annotation = request.args.get('annotation')

    if annotation in ['pleine', 'vide']:
        images = Image.query.filter_by(annotation=annotation).all()
    else:
        images = Image.query.all()

    results = []
    for img in images:
        results.append({
            "id": img.id,
            "filename": img.filename,
            "date_uploaded": img.date_uploaded,
            "annotation": img.annotation,
            "score": img.score,
            "file_size": img.file_size,
            "width": img.width,
            "height": img.height,
            "r_mean": img.r_mean,
            "g_mean": img.g_mean,
            "b_mean": img.b_mean,
            "contrast": img.contrast,
            "saturation_mean": img.saturation_mean,
            "dark_pixel_ratio": img.dark_pixel_ratio,
            "has_bright_spot": img.has_bright_spot
        })

    return jsonify(results)

@app.route('/api/images')
def api_filter_images_paginated():
    annotation = request.args.get('annotation')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    query = Image.query
    if annotation in ['pleine', 'vide']:
        query = query.filter_by(annotation=annotation)

    images = query.order_by(Image.date_uploaded.desc()).paginate(page=page, per_page=limit, error_out=False).items

    results = []
    for img in images:
        results.append({
            "id": img.id,
            "filename": img.filename,
            "date_uploaded": img.date_uploaded,
            "annotation": img.annotation,
            "score": img.score,
            "file_size": img.file_size,
            "width": img.width,
            "height": img.height,
            "r_mean": img.r_mean,
            "g_mean": img.g_mean,
            "b_mean": img.b_mean,
            "contrast": img.contrast,
            "saturation_mean": img.saturation_mean,
            "dark_pixel_ratio": img.dark_pixel_ratio,
            "has_bright_spot": img.has_bright_spot
        })

    return jsonify(results)

@app.route('/api/image/<int:image_id>', methods=['DELETE'])
def api_delete_image(image_id):
    image = Image.query.get_or_404(image_id)

    # Supprimer le fichier physique si présent
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(image)
    db.session.commit()
    return jsonify({"status": "deleted", "id": image_id})

@app.route('/api/image/<int:image_id>')
def api_get_image(image_id):
    img = Image.query.get_or_404(image_id)
    return jsonify({
        "id": img.id,
        "filename": img.filename,
        "date_uploaded": img.date_uploaded,
        "annotation": img.annotation,
        "score": img.score,
        "file_size": img.file_size,
        "width": img.width,
        "height": img.height,
        "r_mean": img.r_mean,
        "g_mean": img.g_mean,
        "b_mean": img.b_mean,
        "contrast": img.contrast,
        "saturation_mean": img.saturation_mean,
        "dark_pixel_ratio": img.dark_pixel_ratio,
        "has_bright_spot": img.has_bright_spot
    })

@app.route('/dashboard')
def dashboard():
    images = Image.query.order_by(Image.date_uploaded.desc()).all()

    nb_images = len(images)
    total_volume_kb = sum(img.file_size for img in images)
    total_volume_mb = total_volume_kb / 1024

    # Approximation : 1 Mo = 5g CO2 (source variable)
    co2_estime = total_volume_mb * 5

    return render_template(
        'dashboard.html',
        images=images,
        nb_images=nb_images,
        volume_mb=round(total_volume_mb, 2),
        co2=round(co2_estime, 1)
    )



@app.route('/delete_rule/<int:rule_id>', methods=['POST'])
def delete_rule(rule_id):
    rule = Rule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    return redirect(url_for('config'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    Image.query.delete()
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/visualisation')
def visualisation():
    # Statistiques nécessaires
    total = Image.query.count()
    pleines = Image.query.filter_by(annotation='pleine').count()
    vides = Image.query.filter_by(annotation='vide').count()
    return render_template("visualisation.html", total=total, pleines=pleines, vides=vides)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)  # Change ici le port

