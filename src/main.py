import os
from datetime import datetime
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'static' / 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zgrany_budget.db'

db = SQLAlchemy(app)

# Ensure upload folder exists
app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'pdf'}


def check_auth(username, password):
    """Check if a username/password combination is valid."""
    return username == 'knurr' and password == 'oink1234'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_size(size_bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_uploaded_files():
    """Get list of uploaded files with metadata."""
    files = []
    upload_folder = app.config['UPLOAD_FOLDER']
    
    if upload_folder.exists():
        for file_path in upload_folder.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'extension': file_path.suffix[1:].lower(),
                    'size': get_file_size(stat.st_size),
                    'uploaded_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                })
    
    # Sort by upload time (newest first)
    files.sort(key=lambda x: x['uploaded_at'], reverse=True)
    return files


@app.route("/")
@auth_required
def index():
    """Main upload page."""
    return render_template('upload.html')


@app.route("/upload", methods=['POST'])
@auth_required
def upload_file():
    """Handle file upload."""
    # Check if file is in request
    if 'file' not in request.files:
        return render_template('partials/upload_status.html', 
                             error='No file provided'), 400
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        return render_template('partials/upload_status.html',
                             error='No file selected'), 400
    
    # Validate file type
    if not allowed_file(file.filename):
        return render_template('partials/upload_status.html',
                             error='Invalid file type. Only .xlsx and .pdf files are allowed'), 400
    
    try:
        # Secure the filename and save
        filename = secure_filename(file.filename)
        file_path = app.config['UPLOAD_FOLDER'] / filename
        
        # Check if file already exists
        if file_path.exists():
            return render_template('partials/upload_status.html',
                                 error=f'File "{filename}" already exists. Please rename or delete the existing file first.'), 400
        
        file.save(file_path)
        
        return render_template('partials/upload_status.html',
                             success=f'File "{filename}" uploaded successfully!')
    
    except Exception as e:
        return render_template('partials/upload_status.html',
                             error=f'Upload failed: {str(e)}'), 500


@app.route("/files")
@auth_required
def list_files():
    """Return list of uploaded files."""
    files = get_uploaded_files()
    return render_template('file_list.html', files=files)


@app.route("/download/<filename>")
@auth_required
def download_file(filename):
    """Download a file."""
    try:
        file_path = app.config['UPLOAD_FOLDER'] / secure_filename(filename)
        
        if not file_path.exists():
            return "File not found", 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return f"Download failed: {str(e)}", 500


@app.route("/delete/<filename>", methods=['DELETE'])
@auth_required
def delete_file(filename):
    """Delete a file."""
    try:
        file_path = app.config['UPLOAD_FOLDER'] / secure_filename(filename)
        
        if not file_path.exists():
            return "File not found", 404
        
        file_path.unlink()
        
        # Return updated file list
        files = get_uploaded_files()
        return render_template('file_list.html', files=files)
    
    except Exception as e:
        return f"Delete failed: {str(e)}", 500


@app.route("/MainPage")
@auth_required
def main_page():
    """Render the main page."""
    return render_template('main_page.html')

@app.route("/health")
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
