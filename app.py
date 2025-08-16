import os
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['LOGO_FOLDER'] = 'logos'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip'}

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def reset_database():
    """Deletes and recreates the database with the correct schema"""
    # Delete existing database if it exists
    if os.path.exists('file_sharing.db'):
        os.remove('file_sharing.db')
        print("Previous database deleted.")
    
    # Create new database
    init_db()
    print("New database created with correct schema.")

def init_db():
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create files table with all necessary fields
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT NOT NULL,
                  original_filename TEXT NOT NULL,
                  user_id INTEGER NOT NULL,
                  is_public BOOLEAN DEFAULT 0,
                  share_token TEXT UNIQUE,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  file_size INTEGER,
                  file_type TEXT,
                  download_count INTEGER DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Create settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  logo_filename TEXT,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("Tables created successfully")

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_logo():
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    c.execute("SELECT logo_filename FROM settings ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_stats(user_id):
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    
    # Total files
    c.execute("SELECT COUNT(*) FROM files WHERE user_id = ?", (user_id,))
    total_files = c.fetchone()[0]
    
    # Public files
    c.execute("SELECT COUNT(*) FROM files WHERE user_id = ? AND is_public = 1", (user_id,))
    public_files = c.fetchone()[0]
    
    # Private files
    private_files = total_files - public_files
    
    # Total size
    c.execute("SELECT SUM(file_size) FROM files WHERE user_id = ?", (user_id,))
    total_size = c.fetchone()[0] or 0
    
    # Total downloads
    c.execute("SELECT SUM(download_count) FROM files WHERE user_id = ?", (user_id,))
    total_downloads = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_files': total_files,
        'public_files': public_files,
        'private_files': private_files,
        'total_size': total_size,
        'total_downloads': total_downloads
    }

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('file_sharing.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        if c.fetchone():
            flash('Username or email already exists', 'error')
            conn.close()
            return redirect(url_for('register'))
        
        # Create new user
        password_hash = generate_password_hash(password)
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  (username, email, password_hash))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    logo = get_logo()
    return render_template('register.html', logo=logo)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('file_sharing.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        user_data = c.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2])
            login_user(user)
            flash('Welcome ' + user_data[1] + '!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials', 'error')
    
    logo = get_logo()
    return render_template('login.html', logo=logo)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    
    # Get user files
    c.execute("""SELECT id, original_filename, is_public, share_token, upload_date, file_size, file_type, download_count 
                 FROM files WHERE user_id = ? ORDER BY upload_date DESC""", (current_user.id,))
    files = c.fetchall()
    conn.close()
    
    # Get statistics
    stats = get_user_stats(current_user.id)
    
    return render_template('dashboard.html', files=files, stats=stats)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file was selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        is_public = request.form.get('is_public') == 'on'
        
        if file.filename == '':
            flash('No file was selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{secrets.token_hex(8)}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Generate sharing token
            share_token = secrets.token_urlsafe(16)
            
            # Get file information
            file_size = os.path.getsize(filepath)
            file_type = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
            
            # Save to database
            conn = sqlite3.connect('file_sharing.db')
            c = conn.cursor()
            c.execute("""INSERT INTO files (filename, original_filename, user_id, is_public, share_token, file_size, file_type, upload_date)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                      (unique_filename, filename, current_user.id, is_public, share_token, file_size, file_type, datetime.now()))
            conn.commit()
            conn.close()
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('File type not allowed', 'error')
    
    return render_template('upload.html')

@app.route('/file/<token>')
def shared_file(token):
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE share_token = ?", (token,))
    file_data = c.fetchone()
    conn.close()
    
    if not file_data:
        abort(404)
    
    # Check if file is public or user is the owner
    if not file_data[4] and (not current_user.is_authenticated or current_user.id != file_data[3]):
        abort(403)
    
    logo = get_logo()
    return render_template('view_file.html', file=file_data, logo=logo)

@app.route('/download/<token>')
def download_file(token):
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE share_token = ?", (token,))
    file_data = c.fetchone()
    
    if not file_data:
        conn.close()
        abort(404)
    
    # Check permissions
    if not file_data[4] and (not current_user.is_authenticated or current_user.id != file_data[3]):
        conn.close()
        abort(403)
    
    # Increment download counter
    c.execute("UPDATE files SET download_count = download_count + 1 WHERE id = ?", (file_data[0],))
    conn.commit()
    conn.close()
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_data[1], 
                               as_attachment=True, download_name=file_data[2])

@app.route('/toggle_public/<int:file_id>')
@login_required
def toggle_public(file_id):
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    
    # Check ownership
    c.execute("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, current_user.id))
    file_data = c.fetchone()
    
    if not file_data:
        conn.close()
        abort(403)
    
    # Change privacy status
    new_status = not file_data[4]
    c.execute("UPDATE files SET is_public = ? WHERE id = ?", (new_status, file_id))
    conn.commit()
    conn.close()
    
    status_text = "public" if new_status else "private"
    flash(f'File changed to {status_text}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    conn = sqlite3.connect('file_sharing.db')
    c = conn.cursor()
    
    # Check ownership
    c.execute("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, current_user.id))
    file_data = c.fetchone()
    
    if not file_data:
        conn.close()
        abort(403)
    
    # Delete file from system
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_data[1])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete from database
    c.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()
    
    flash('File deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename != '' and allowed_file(logo.filename):
                filename = secure_filename(logo.filename)
                unique_filename = f"logo_{secrets.token_hex(4)}_{filename}"
                filepath = os.path.join(app.config['LOGO_FOLDER'], unique_filename)
                logo.save(filepath)
                
                # Save to database
                conn = sqlite3.connect('file_sharing.db')
                c = conn.cursor()
                c.execute("INSERT INTO settings (logo_filename) VALUES (?)", (unique_filename,))
                conn.commit()
                conn.close()
                
                flash('Logo updated successfully', 'success')
                return redirect(url_for('settings'))
    
    stats = get_user_stats(current_user.id)
    logo = get_logo()
    return render_template('settings.html', logo=logo, stats=stats)

@app.route('/logo/<filename>')
def serve_logo(filename):
    return send_from_directory(app.config['LOGO_FOLDER'], filename)

# Route to reset database (DEVELOPMENT ONLY)
@app.route('/reset-db')
def reset_db():
    reset_database()
    flash('Database reset successfully', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Check if we need to reset the database
   
    app.run(debug=True, port=5000)