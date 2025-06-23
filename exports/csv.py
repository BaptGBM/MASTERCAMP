from flask import Response, jsonify
import csv

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

@app.route('/export/json')
def export_json():
    images = Image.query.all()
    data = [
        {
            "id": img.id,
            "filename": img.filename,
            "date": img.date_uploaded.isoformat(),
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
        }
        for img in images
    ]
    return jsonify(data)
