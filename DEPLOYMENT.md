# EY File Sharing - Deployment Guide for PythonAnywhere

## 📋 Prerequisites

- PythonAnywhere account (Free or Paid)
- Python 3.8+ support
- Basic knowledge of PythonAnywhere interface

## 🚀 Deployment Steps

### 1. Upload Files to PythonAnywhere

1. **Option A: Git Clone (Recommended)**
   ```bash
   cd ~
   git clone [your-repo-url] file-sharing
   cd file-sharing
   ```

2. **Option B: File Upload**
   - Upload all files via PythonAnywhere Files interface
   - Ensure the folder structure is maintained

### 2. Install Dependencies

Open a **Bash console** in PythonAnywhere:

```bash
cd ~/file-sharing
pip3.10 install --user -r requirements.txt
```

### 3. Initial Setup

Run the setup script to initialize directories and database:

```bash
cd ~/file-sharing
python3.10 setup_pythonanywhere.py
```

### 4. Configure Flask App

1. **Edit flask_app.py**:
   - Open `flask_app.py`
   - Change line 10: Replace `yourusername` with your actual PythonAnywhere username
   ```python
   path = '/home/YOUR_USERNAME/file-sharing'  # Update this line
   ```

2. **Set Environment Variables** (Optional but recommended):
   - Create a `.env` file in your project directory:
   ```bash
   SECRET_KEY=your-super-secret-key-here-make-it-very-long-and-random
   FLASK_CONFIG=production
   ```

### 5. Configure Web App in PythonAnywhere

1. **Go to Web tab** in your PythonAnywhere dashboard
2. **Click "Add a new web app"**
3. **Choose "Manual configuration"**
4. **Select Python 3.10**
5. **Configure the following**:

   **Source code**: `/home/yourusername/file-sharing`
   
   **WSGI configuration file**: Click to edit and replace content with:
   ```python
   import sys
   import os
   
   # Add your project directory to Python path
   path = '/home/yourusername/file-sharing'
   if path not in sys.path:
       sys.path.insert(0, path)
   
   # Import your Flask app
   from flask_app import application
   ```

### 6. Static Files Configuration

In the **Web tab**, configure static files:

- **URL**: `/static/`
- **Directory**: `/home/yourusername/file-sharing/static/`

### 7. Security Configuration

1. **Change Secret Key**:
   - Edit `config.py` and update the SECRET_KEY
   - Or set it as an environment variable

2. **File Permissions**:
   ```bash
   chmod 755 ~/file-sharing
   chmod -R 755 ~/file-sharing/uploads
   chmod -R 755 ~/file-sharing/logos
   ```

### 8. Test and Deploy

1. **Reload your web app** in the Web tab
2. **Visit your domain**: `https://yourusername.pythonanywhere.com`
3. **Test the application**:
   - Register a new account
   - Upload a file
   - Test file sharing

## 🛠️ Troubleshooting

### Common Issues:

1. **Import Errors**:
   - Check that all dependencies are installed
   - Verify Python path in flask_app.py

2. **Database Issues**:
   - Run setup_pythonanywhere.py again
   - Check file permissions

3. **File Upload Issues**:
   - Verify uploads directory exists and is writable
   - Check MAX_CONTENT_LENGTH setting

4. **Static Files Not Loading**:
   - Verify static files configuration in Web tab
   - Check file paths

### Debug Mode:

For debugging, temporarily enable debug mode by editing `flask_app.py`:
```python
# For debugging only - disable in production
os.environ['FLASK_DEBUG'] = 'True'
```

## 📁 Directory Structure

```
/home/yourusername/file-sharing/
├── app_factory.py          # Application factory
├── flask_app.py           # PythonAnywhere entry point
├── config.py              # Configuration settings
├── setup_pythonanywhere.py # Setup script
├── requirements.txt       # Python dependencies
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── uploads/              # User uploaded files
├── logos/                # Application logos
└── file_sharing.db       # SQLite database
```

## 🔒 Security Notes

1. **Change the SECRET_KEY** in production
2. **Disable debug mode** in production
3. **Set appropriate file permissions**
4. **Consider using environment variables** for sensitive data
5. **Regularly backup your database** and uploaded files

## 📊 Monitoring

- Check **Error logs** in PythonAnywhere Web tab
- Monitor **CPU usage** if on free plan
- Set up **backup routine** for database and files

## 🔄 Updates

To update your application:

1. Pull latest changes (if using Git):
   ```bash
   cd ~/file-sharing
   git pull
   ```

2. Install new dependencies (if any):
   ```bash
   pip3.10 install --user -r requirements.txt
   ```

3. Reload web app in PythonAnywhere dashboard

## 📞 Support

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Flask Documentation: https://flask.palletsprojects.com/
- Application Issues: Check error logs in Web tab