

from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for, flash
import json
import os
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'order_1'
DATA_FILE = 'users.json'
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')


def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_users(users):
    with open(DATA_FILE, 'w') as file:
        json.dump(users, file, indent=4)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return "Username and password are required", 400

        users = load_users()

        if username in users:
            return "Username already exists", 400

        users[username] = {'password': password}
        save_users(users)

        # Create user folder
        user_folder = os.path.join(UPLOAD_FOLDER, username)
        os.makedirs(user_folder, exist_ok=True)

        return "Signup successful", 200

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        users = load_users()

        if username not in users or users[username]['password'] != password:
            return "Invalid username or password", 400

        return "Login successful", 200

    return render_template('login.html')


@app.route('/dashboard/<username>', methods=['GET', 'POST', 'DELETE'])
def dashboard(username):
    if request.method == 'POST':
        data = request.get_json()
        project_name = data.get('project_name')

        if not project_name:
            return "Project name is required", 400

        user_folder = os.path.join(UPLOAD_FOLDER, username)
        project_folder = os.path.join(user_folder, project_name)
        os.makedirs(project_folder, exist_ok=True)

        return "Project created", 200

    elif request.method == 'GET':
        user_folder = os.path.join(UPLOAD_FOLDER, username)
        folders = [folder for folder in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, folder))]
        return render_template('dashboard.html', username=username, folders=folders)

    elif request.method == 'DELETE':
        project_name = request.args.get('project_name')
        if not project_name:
            return "Project name is required", 400

        user_folder = os.path.join(UPLOAD_FOLDER, username)
        project_folder = os.path.join(user_folder, project_name)

        if os.path.exists(project_folder):
            shutil.rmtree(project_folder)
            return "Project deleted", 200
        else:
            return "Project not found", 404


@app.route('/dashboard/<username>/<project_name>', methods=['GET', 'POST', 'DELETE'])
def project(username, project_name):
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    project_folder = os.path.join(user_folder, project_name)

    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(project_folder, filename))
            return "File uploaded", 200

    if os.path.exists(project_folder):
        files = os.listdir(project_folder)
        return render_template('project.html', username=username, project_name=project_name, files=files)
    else:
        return "Project not found", 404


@app.route('/dashboard/<username>/<project_name>/run')
def run_project(username, project_name):
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    project_folder = os.path.join(user_folder, project_name)
    index_file = os.path.join(project_folder, 'index.html')

    if os.path.exists(index_file):
        # Serve the index.html file from the project folder
        return send_from_directory(project_folder, 'index.html')
    else:
        return render_template('Error404.html')


@app.route('/dashboard/<username>/<project_name>/edit', methods=['GET', 'POST'])
def edit(username, project_name):
    filename = request.args.get('filename')
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    project_folder = os.path.join(user_folder, project_name)
    file_path = os.path.join(project_folder, filename)

    if request.method == 'POST':
        content = request.form['file_content']
        with open(file_path, 'w') as file:
            file.write(content)
        return redirect(url_for('project', username=username, project_name=project_name))

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('edit.html', username=username, project_name=project_name, filename=filename, content=content)
    else:
        return "File not found", 404


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'html', 'css', 'js', 'png', 'jpg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
