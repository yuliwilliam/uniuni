from datetime import timedelta
from uuid import uuid4

from flask import Flask, render_template, request, send_from_directory, jsonify, session, redirect, url_for
import os
import zipfile
import shutil

from constants import PASSWORD, APP_SECURITY_KEY, FILENAME_SPLITTER, UPLOAD_FOLDER, OUTPUT_FOLDER, ZIP_FOLDER, FOLDERS
from city_code_splitter.excel import split_by_city_code

app = Flask(__name__)

# Ensure the upload, output, and zip folders exist
for folder in FOLDERS:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.secret_key = APP_SECURITY_KEY  # Change this to a random, secure key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)


def zip_files(file_paths, zip_name):
    zip_path = os.path.join(ZIP_FOLDER, zip_name)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))
    return zip_path


def clean_folders():
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, ZIP_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid password")
    return render_template('login.html')


@app.route('/index', methods=['GET'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    clean_folders()
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files[]')
    zip_names = []
    for file in files:
        if file and file.filename.endswith('.xlsx'):
            file_path = os.path.join(UPLOAD_FOLDER, f"{str(uuid4())}{FILENAME_SPLITTER}{file.filename}")
            file.save(file_path)
            output_files = split_by_city_code(file_path)

            # Zip the split files
            zip_name = f'{str(uuid4())}{FILENAME_SPLITTER}{file.filename.split(".")[0]}.zip'
            zip_path = zip_files(output_files, zip_name)
            zip_names.append(zip_name)

    # Clean up the output folder after zipping
    shutil.rmtree(OUTPUT_FOLDER)
    os.makedirs(OUTPUT_FOLDER)

    return jsonify({'zip_files': zip_names})


@app.route('/download/<filename>')
def download_file(filename):
    new_filename = filename.split(FILENAME_SPLITTER)[1]  # Replace with your desired filename
    return send_from_directory(ZIP_FOLDER, filename, download_name=new_filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
