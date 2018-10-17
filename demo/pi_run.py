import os
from flask import Flask, render_template, request, url_for, jsonify
from werkzeug import secure_filename

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/confirm_page', methods=['POST'])
def confirm():
    file = request.files['upload_file']
    filename = secure_filename(file.filename)
    file.save(os.path.join('static/uploads', filename))
    return render_template('confirm.html', FILENAME='uploads/%s' % filename)

@app.route('/api/print', methods=['POST'])
def api_print():
    device = 'hp_colorJet'
    filename = request.form.get('filename')
    return jsonify({'code': os.system('lp -d %s %s' % (device, filename))})

app.run(debug=True)
