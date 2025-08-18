#!/usr/bin/env python3
"""
Script to update app.py to use the new database wrapper
This script replaces all direct SQLite calls with wrapper calls
"""
import re

def update_app_py():
    # Read the current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    with open('app_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Upload route update
    upload_pattern = r"@app\.route\('/upload', methods=\['GET', 'POST'\]\)\s*@login_required\s*def upload\(\):\s*.*?return render_template\('upload\.html'\)"
    upload_replacement = """@app.route('/upload', methods=['GET', 'POST'])
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
    
    return render_template('upload.html')"""
    
    content = re.sub(upload_pattern, upload_replacement, content, flags=re.DOTALL)
    
    # Initialize database at app startup
    init_pattern = r"if __name__ == '__main__':\s*.*?app\.run\(debug=True, port=5000\)"
    init_replacement = """# Initialize database on startup
init_app_database()

if __name__ == '__main__':
    app.run(debug=True, port=5000)"""
    
    content = re.sub(init_pattern, init_replacement, content, flags=re.DOTALL)
    
    # Write updated content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ app.py updated successfully")
    print("📄 Original backed up as app_backup.py")

if __name__ == "__main__":
    update_app_py()