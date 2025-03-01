from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'supersecretkey'
db = SQLAlchemy(app)

# Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Model
class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)

# User Model for Admin
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Hardcoded admin user (for simplicity)
ADMIN_USER = {'id': 1, 'username': 'admin', 'password': 'admin123'}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Routes
@app.route('/')
def home():
    materials = StudyMaterial.query.all()

    # Remove database records for missing files
    for material in materials:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], material.file_path.split('/')[-1])
        if not os.path.exists(file_path):  # If the file doesn't exist
            db.session.delete(material)
    
    db.session.commit()  # Save changes after loop

    materials = StudyMaterial.query.all()  # Reload after cleanup
    return render_template('index.html', materials=materials)


@app.route('/view_pdf/<path:filename>')
def view_pdf(filename):
    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])  # Get full path
    file_path = os.path.join(upload_folder, filename)

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")  # Debugging log
        return "File not found", 404  # Return a proper error message

    return send_from_directory(upload_folder, filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Ensure forward slashes for URL compatibility
    file_path = file_path.replace("\\", "/")  # Convert Windows backslashes to forward slashes

    new_material = StudyMaterial(
        title=request.form.get('title'),
        subject=request.form.get('subject'),
        file_type=filename.split('.')[-1].upper(),
        file_path=file_path
    )
    db.session.add(new_material)
    db.session.commit()
    flash('File uploaded successfully', 'success')
    return redirect(url_for('dashboard'))



@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_file(id):
    material = StudyMaterial.query.get_or_404(id)
    os.remove(material.file_path)
    db.session.delete(material)
    db.session.commit()
    flash('File deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER['username'] and password == ADMIN_USER['password']:
            user = User(ADMIN_USER['id'])
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    materials = StudyMaterial.query.all()

    # Remove database entries for missing files
    for material in materials:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], material.file_path.split('/')[-1])
        if not os.path.exists(file_path):  # If the file is missing
            db.session.delete(material)
    
    db.session.commit()  # Save changes after loop

    materials = StudyMaterial.query.all()  # Reload the updated list
    return render_template('dashboard.html', materials=materials)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Initialize Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)