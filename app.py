import os
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from db_wrapper import db

# CRITICAL: Import deployment initialization FIRST
from deploy_init import get_deployment_paths

# Initialize deployment paths with forced configuration
print("[APP] Initializing deployment configuration...")
DEPLOYMENT_PATHS = get_deployment_paths()
BASE_DIR = DEPLOYMENT_PATHS['base_dir']

print(f"[APP] Using BASE_DIR: {BASE_DIR}")
print(f"[APP] Current working directory: {os.getcwd()}")

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
# Use deployment paths to ensure correct directories
app.config['UPLOAD_FOLDER'] = DEPLOYMENT_PATHS['uploads']
app.config['LOGO_FOLDER'] = DEPLOYMENT_PATHS['logos']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip'}

print(f"[APP] Upload folder configured: {app.config['UPLOAD_FOLDER']}")
print(f"[APP] Logo folder configured: {app.config['LOGO_FOLDER']}")

# Directory structure is already created by deployment initialization
print("[APP] Skipping directory creation - handled by deployment initialization")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database initialization
def init_app_database():
    """Initialize database when app starts"""
    # Use the deployment-configured database path
    db_path = DEPLOYMENT_PATHS['database']
    print(f"[APP] Setting database path to: {db_path}")
    
    # Force the database service to use our specific path
    db.db_service.db_path = db_path
    
    # Verify the path is set correctly
    print(f"[APP] Database service path: {db.db_service.db_path}")
    
    if not db.initialize():
        print(f"[APP] [ERROR] Failed to initialize database at: {db_path}")
        return False
    
    print(f"[APP] [OK] Database initialized successfully at: {db_path}")
    
    # Double-check the database was created in the right place
    if os.path.exists(db_path):
        print(f"[APP] [OK] Database file confirmed at: {db_path}")
        
        # Verify the database is in the correct project directory
        if db_path.startswith(BASE_DIR):
            print(f"[APP] [OK] Database is correctly located within project directory")
        else:
            print(f"[APP] [WARNING] Database is outside project directory!")
            print(f"[APP]   Expected prefix: {BASE_DIR}")
            print(f"[APP]   Actual path: {db_path}")
    else:
        print(f"[APP] [ERROR] Database file NOT found at expected location: {db_path}")
    
    return True

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user_by_id(user_id)
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['email'])
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_logo():
    return db.get_logo()

def get_user_stats(user_id):
    return db.get_user_stats(user_id)

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
        
        # Check if user exists
        if db.user_exists(username, email):
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        password_hash = generate_password_hash(password)
        db.create_user(username, email, password_hash)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    logo = get_logo()
    return render_template('register.html', logo=logo)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = db.get_user_by_username_or_email(username)
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['email'])
            login_user(user)
            flash('Welcome ' + user_data['username'] + '!', 'success')
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
    # Get user files
    files = db.get_user_files(current_user.id)
    
    # Get user bundles
    bundles = db.get_user_bundles(current_user.id)
    
    # Get statistics
    stats = get_user_stats(current_user.id)
    
    return render_template('dashboard.html', files=files, bundles=bundles, stats=stats)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file was selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        is_public = request.form.get('is_public') == 'on'
        transaction_number = request.form.get('transaction_number')
        
        if file.filename == '':
            flash('No file was selected', 'error')
            return redirect(request.url)
        
        if not transaction_number:
            flash('Transaction number is required', 'error')
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
            db.create_file(unique_filename, filename, current_user.id, is_public, share_token, 
                          file_size, file_type, transaction_number)
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('File type not allowed', 'error')
    
    return render_template('upload.html')

@app.route('/file/<token>')
def shared_file(token):
    file_data = db.get_file_by_token(token)
    
    if not file_data:
        abort(404)
    
    # Check if file is public or user is the owner
    if not file_data['is_public'] and (not current_user.is_authenticated or current_user.id != file_data['user_id']):
        abort(403)
    
    # Check if this file belongs to a bundle (get from URL parameter)
    bundle_token = request.args.get('from_bundle')
    bundle_data = None
    if bundle_token:
        bundle_data = db.get_bundle_by_token(bundle_token)
        # Verify the file is actually in this bundle
        if bundle_data:
            bundle_files = db.get_bundle_files(bundle_data['id'])
            file_ids_in_bundle = [f['id'] for f in bundle_files]
            if file_data['id'] not in file_ids_in_bundle:
                bundle_data = None  # File not in this bundle
    
    logo = get_logo()
    # Convert to tuple for template compatibility
    file_tuple = (file_data['id'], file_data['filename'], file_data['original_filename'], 
                  file_data['user_id'], file_data['is_public'], file_data['share_token'],
                  file_data['upload_date'], file_data['file_size'], file_data['file_type'],
                  file_data['download_count'], file_data['transaction_number'])
    return render_template('view_file.html', file=file_tuple, logo=logo, bundle=bundle_data)

@app.route('/view/<token>')
def view_file_content(token):
    """Route to view file content in browser (for PDFs and images)"""
    file_data = db.get_file_by_token(token)
    
    if not file_data:
        abort(404)
    
    # Check permissions
    if not file_data['is_public'] and (not current_user.is_authenticated or current_user.id != file_data['user_id']):
        abort(403)
    
    # Get file extension
    file_extension = file_data['file_type'].lower() if file_data['file_type'] else ''
    
    # Set appropriate content type for inline display
    if file_extension == 'pdf':
        from flask import Response
        import os
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_data['filename'])
        if not os.path.exists(file_path):
            abort(404)
        
        def generate():
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    yield data
        
        return Response(
            generate(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename="{file_data["original_filename"]}"',
                'Content-Type': 'application/pdf',
                'X-Frame-Options': 'SAMEORIGIN',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        )
    elif file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            file_data['filename'], 
            as_attachment=False,
            download_name=file_data['original_filename']
        )
    else:
        # For other file types, redirect to download
        return redirect(url_for('download_file', token=token))

@app.route('/download/<token>')
def download_file(token):
    file_data = db.get_file_by_token(token)
    
    if not file_data:
        abort(404)
    
    # Check permissions
    if not file_data['is_public'] and (not current_user.is_authenticated or current_user.id != file_data['user_id']):
        abort(403)
    
    # Increment download counter only for actual downloads
    db.increment_download_count(file_data['id'])
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_data['filename'], 
                               as_attachment=True, download_name=file_data['original_filename'])

@app.route('/toggle_public/<int:file_id>')
@login_required
def toggle_public(file_id):
    # Check ownership and get file data
    file_data = db.get_file_by_id(file_id)
    
    if not file_data or file_data['user_id'] != current_user.id:
        abort(403)
    
    # Change privacy status
    new_status = not file_data['is_public']
    db.update_file_privacy(file_id, new_status)
    
    if new_status:
        # File is now public
        flash(f'File "{file_data["original_filename"]}" is now public and can be shared', 'success')
    else:
        # File is now private
        flash(f'File "{file_data["original_filename"]}" is now private - public access has been revoked', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    # Check ownership and get file data
    file_data = db.get_file_by_id(file_id)
    
    if not file_data or file_data['user_id'] != current_user.id:
        abort(403)
    
    # Delete file from system
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_data['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Delete from database
    db.delete_file(file_id)
    
    flash('File deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/rename_file/<int:file_id>', methods=['GET', 'POST'])
@login_required
def rename_file(file_id):
    # Check ownership and get file data
    file_data = db.get_file_by_id(file_id)
    
    if not file_data or file_data['user_id'] != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        new_name = request.form.get('new_name')
        
        if not new_name or not new_name.strip():
            flash('File name cannot be empty', 'error')
            return redirect(request.url)
        
        # Update file name in database
        db.update_file_name(file_id, new_name.strip())
        
        flash(f'File name updated to "{new_name}"', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('rename_file.html', file=file_data)

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
                db.set_logo(unique_filename)
                
                flash('Logo updated successfully', 'success')
                return redirect(url_for('settings'))
    
    stats = get_user_stats(current_user.id)
    logo = get_logo()
    return render_template('settings.html', logo=logo, stats=stats)

@app.route('/logo/<filename>')
def serve_logo(filename):
    return send_from_directory(app.config['LOGO_FOLDER'], filename)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('change_password'))
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return redirect(url_for('change_password'))
        
        # Verify current password
        current_password_hash = db.get_user_password_hash(current_user.id)
        
        if not current_password_hash or not check_password_hash(current_password_hash, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('change_password'))
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        db.update_user_password(current_user.id, new_password_hash)
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('change_password.html')

@app.route('/create-bundle', methods=['GET', 'POST'])
@login_required
def create_bundle():
    if request.method == 'POST':
        bundle_name = request.form.get('bundle_name')
        transaction_number = request.form.get('transaction_number')
        selected_files = request.form.getlist('selected_files')
        is_public = request.form.get('is_public') == 'on'
        
        if not bundle_name or not transaction_number or not selected_files:
            flash('Please fill all fields and select at least one file', 'error')
            return redirect(request.url)
        
        # Generate sharing token
        share_token = secrets.token_urlsafe(16)
        
        # Create bundle
        bundle_id = db.create_bundle(bundle_name, transaction_number, current_user.id, is_public, share_token)
        
        if bundle_id:
            # Add files to bundle
            for file_id in selected_files:
                db.add_file_to_bundle(bundle_id, file_id)
            
            # Get the count of files actually added
            bundle_files = db.get_bundle_files(bundle_id)
            file_count = len(bundle_files)
            
            flash(f'Bundle "{transaction_number}" created successfully with {file_count} file{"s" if file_count != 1 else ""}!', 'success')
        else:
            flash('Error creating bundle', 'error')
            
        return redirect(url_for('dashboard'))
    
    # Get user's files for selection
    files = db.get_user_files_for_bundle(current_user.id)
    
    return render_template('create_bundle.html', files=files)

@app.route('/bundle/<token>')
def shared_bundle(token):
    # Get bundle info
    bundle_data = db.get_bundle_by_token(token)
    
    if not bundle_data:
        abort(404)
    
    # Check permissions
    if not bundle_data['is_public'] and (not current_user.is_authenticated or current_user.id != bundle_data['user_id']):
        abort(403)
    
    # Get files in bundle
    files = db.get_bundle_files(bundle_data['id'])
    
    logo = get_logo()
    return render_template('view_bundle.html', bundle=bundle_data, files=files, logo=logo)

@app.route('/download-bundle/<token>')
def download_bundle(token):
    import zipfile
    import tempfile
    
    # Get bundle info
    bundle_data = db.get_bundle_by_token(token)
    
    if not bundle_data:
        abort(404)
    
    # Check permissions
    if not bundle_data['is_public'] and (not current_user.is_authenticated or current_user.id != bundle_data['user_id']):
        abort(403)
    
    # Get files in bundle
    files = db.get_bundle_files(bundle_data['id'])
    
    # Increment download counter
    db.increment_bundle_download_count(bundle_data['id'])
    
    # Create zip file
    temp_dir = tempfile.mkdtemp()
    zip_filename = f"{bundle_data['transaction_number']}.zip"  # Use transaction number as filename
    zip_path = os.path.join(temp_dir, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        for file_data in files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_data['filename'])
            if os.path.exists(file_path):
                # Use original filename in zip
                zip_file.write(file_path, file_data['original_filename'])
    
    return send_from_directory(temp_dir, zip_filename, as_attachment=True, download_name=zip_filename)

@app.route('/toggle_bundle_public/<int:bundle_id>')
@login_required
def toggle_bundle_public(bundle_id):
    # Check ownership and get bundle data
    bundle_data = db.get_bundle_by_id(bundle_id)
    
    if not bundle_data or bundle_data['user_id'] != current_user.id:
        abort(403)
    
    # Change privacy status
    new_status = not bundle_data['is_public']
    db.update_bundle_privacy(bundle_id, new_status)
    
    if new_status:
        # Bundle is now public
        flash(f'Bundle "{bundle_data["transaction_number"]}" is now public and can be shared', 'success')
    else:
        # Bundle is now private
        flash(f'Bundle "{bundle_data["transaction_number"]}" is now private - public access has been revoked', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/edit_bundle/<int:bundle_id>', methods=['GET', 'POST'])
@login_required
def edit_bundle(bundle_id):
    # Check ownership and get bundle data
    bundle_data = db.get_bundle_by_id(bundle_id)
    
    if not bundle_data or bundle_data['user_id'] != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        bundle_name = request.form.get('bundle_name')
        transaction_number = request.form.get('transaction_number')
        selected_files = request.form.getlist('selected_files')
        is_public = request.form.get('is_public') == 'on'
        
        if not bundle_name or not transaction_number:
            flash('Bundle name and transaction number are required', 'error')
            return redirect(request.url)
        
        # Update bundle info
        db.update_bundle_info(bundle_id, bundle_name, transaction_number, is_public)
        
        # Update files in bundle - first remove all existing files
        db.remove_all_files_from_bundle(bundle_id)
        
        # Add selected files to bundle
        if selected_files:
            for file_id in selected_files:
                db.add_file_to_bundle(bundle_id, file_id)
        
        flash(f'Bundle "{transaction_number}" updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get user's files for selection
    all_files = db.get_user_files_for_bundle(current_user.id)
    
    # Get current files in bundle
    current_files = db.get_bundle_files(bundle_id)
    current_file_ids = [f['id'] for f in current_files]
    
    return render_template('edit_bundle.html', 
                         bundle=bundle_data, 
                         files=all_files, 
                         current_file_ids=current_file_ids)

@app.route('/delete_bundle/<int:bundle_id>')
@login_required
def delete_bundle(bundle_id):
    # Check ownership and get bundle data
    bundle_data = db.get_bundle_by_id(bundle_id)
    
    if not bundle_data or bundle_data['user_id'] != current_user.id:
        abort(403)
    
    # Delete bundle from database (this will also remove bundle_files entries via foreign key)
    db.delete_bundle(bundle_id)
    
    flash('Bundle deleted successfully', 'success')
    return redirect(url_for('dashboard'))

# Route to reset database (DEVELOPMENT ONLY)
@app.route('/reset-db')
def reset_db():
    reset_database()
    flash('Database reset successfully', 'success')
    return redirect(url_for('login'))


# Initialize database on startup
init_app_database()

if __name__ == '__main__':
    app.run(debug=True, port=5000)