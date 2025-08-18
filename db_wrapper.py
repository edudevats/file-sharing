#!/usr/bin/env python3
"""
Database Wrapper for EY File Sharing Application
Provides high-level database operations using the database service
"""
from database_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

class DatabaseWrapper:
    def __init__(self):
        self.db_service = DatabaseService()
    
    def initialize(self):
        """Initialize database - call this once at app startup"""
        try:
            self.db_service.initialize_database()
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    # User operations
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return self.db_service.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
            fetch_one=True
        )
    
    def get_user_by_username_or_email(self, username):
        """Get user by username or email"""
        return self.db_service.execute_query(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, username),
            fetch_one=True
        )
    
    def create_user(self, username, email, password_hash):
        """Create new user"""
        return self.db_service.execute_query(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
    
    def user_exists(self, username, email):
        """Check if user exists"""
        result = self.db_service.execute_query(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
            fetch_one=True
        )
        return result is not None
    
    # File operations
    def create_file(self, filename, original_filename, user_id, is_public, share_token, 
                   file_size, file_type, transaction_number=None):
        """Create new file record"""
        return self.db_service.execute_query(
            """INSERT INTO files (filename, original_filename, user_id, is_public, 
               share_token, file_size, file_type, transaction_number) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, original_filename, user_id, is_public, share_token, 
             file_size, file_type, transaction_number)
        )
    
    def get_file_by_token(self, token):
        """Get file by share token"""
        return self.db_service.execute_query(
            "SELECT * FROM files WHERE share_token = ?",
            (token,),
            fetch_one=True
        )
    
    def get_file_by_id(self, file_id):
        """Get file by ID"""
        return self.db_service.execute_query(
            "SELECT * FROM files WHERE id = ?",
            (file_id,),
            fetch_one=True
        )
    
    def get_user_files(self, user_id):
        """Get all files for a user"""
        return self.db_service.execute_query(
            """SELECT id, original_filename, is_public, share_token, upload_date, 
               file_size, file_type, download_count, transaction_number 
               FROM files WHERE user_id = ? ORDER BY upload_date DESC""",
            (user_id,),
            fetch=True
        )
    
    def update_file_privacy(self, file_id, is_public):
        """Update file privacy setting"""
        return self.db_service.execute_query(
            "UPDATE files SET is_public = ? WHERE id = ?",
            (is_public, file_id)
        )
    
    def update_file_name(self, file_id, new_name):
        """Update file original filename"""
        return self.db_service.execute_query(
            "UPDATE files SET original_filename = ? WHERE id = ?",
            (new_name, file_id)
        )
    
    def delete_file(self, file_id):
        """Delete file record"""
        return self.db_service.execute_query(
            "DELETE FROM files WHERE id = ?",
            (file_id,)
        )
    
    def increment_download_count(self, file_id):
        """Increment file download counter"""
        return self.db_service.execute_query(
            "UPDATE files SET download_count = download_count + 1 WHERE id = ?",
            (file_id,)
        )
    
    def verify_file_ownership(self, file_id, user_id):
        """Verify if user owns the file"""
        result = self.db_service.execute_query(
            "SELECT id FROM files WHERE id = ? AND user_id = ?",
            (file_id, user_id),
            fetch_one=True
        )
        return result is not None
    
    # Bundle operations
    def create_bundle(self, bundle_name, transaction_number, user_id, is_public, share_token):
        """Create new file bundle"""
        self.db_service.execute_query(
            """INSERT INTO file_bundles (bundle_name, transaction_number, user_id, 
               is_public, share_token) VALUES (?, ?, ?, ?, ?)""",
            (bundle_name, transaction_number, user_id, is_public, share_token)
        )
        
        # Get the bundle ID
        result = self.db_service.execute_query(
            "SELECT last_insert_rowid()",
            fetch_one=True
        )
        return result[0] if result else None
    
    def add_file_to_bundle(self, bundle_id, file_id):
        """Add file to bundle"""
        return self.db_service.execute_query(
            "INSERT INTO bundle_files (bundle_id, file_id) VALUES (?, ?)",
            (bundle_id, file_id)
        )
    
    def get_bundle_by_token(self, token):
        """Get bundle by share token"""
        return self.db_service.execute_query(
            "SELECT * FROM file_bundles WHERE share_token = ?",
            (token,),
            fetch_one=True
        )
    
    def get_bundle_files(self, bundle_id):
        """Get all files in a bundle"""
        return self.db_service.execute_query(
            """SELECT f.* FROM files f 
               JOIN bundle_files bf ON f.id = bf.file_id 
               WHERE bf.bundle_id = ? ORDER BY f.upload_date""",
            (bundle_id,),
            fetch=True
        )
    
    def increment_bundle_download_count(self, bundle_id):
        """Increment bundle download counter"""
        return self.db_service.execute_query(
            "UPDATE file_bundles SET download_count = download_count + 1 WHERE id = ?",
            (bundle_id,)
        )
    
    def get_user_files_for_bundle(self, user_id):
        """Get user files for bundle creation"""
        return self.db_service.execute_query(
            """SELECT id, original_filename, transaction_number, file_type, file_size 
               FROM files WHERE user_id = ? ORDER BY upload_date DESC""",
            (user_id,),
            fetch=True
        )
    
    def get_user_bundles(self, user_id):
        """Get all bundles for a user with file count"""
        return self.db_service.execute_query(
            """SELECT fb.id, fb.bundle_name, fb.transaction_number, fb.is_public, fb.share_token, 
               fb.created_date, fb.download_count,
               COUNT(bf.file_id) as file_count
               FROM file_bundles fb 
               LEFT JOIN bundle_files bf ON fb.id = bf.bundle_id
               WHERE fb.user_id = ? 
               GROUP BY fb.id, fb.bundle_name, fb.transaction_number, fb.is_public, fb.share_token, 
                        fb.created_date, fb.download_count
               ORDER BY fb.created_date DESC""",
            (user_id,),
            fetch=True
        )
    
    def get_bundle_by_id(self, bundle_id):
        """Get bundle by ID"""
        return self.db_service.execute_query(
            "SELECT * FROM file_bundles WHERE id = ?",
            (bundle_id,),
            fetch_one=True
        )
    
    def update_bundle_privacy(self, bundle_id, is_public):
        """Update bundle privacy setting"""
        return self.db_service.execute_query(
            "UPDATE file_bundles SET is_public = ? WHERE id = ?",
            (is_public, bundle_id)
        )
    
    def update_bundle_info(self, bundle_id, bundle_name, transaction_number, is_public):
        """Update bundle information"""
        return self.db_service.execute_query(
            """UPDATE file_bundles SET bundle_name = ?, transaction_number = ?, is_public = ? 
               WHERE id = ?""",
            (bundle_name, transaction_number, is_public, bundle_id)
        )
    
    def remove_all_files_from_bundle(self, bundle_id):
        """Remove all files from a bundle"""
        return self.db_service.execute_query(
            "DELETE FROM bundle_files WHERE bundle_id = ?",
            (bundle_id,)
        )
    
    def delete_bundle(self, bundle_id):
        """Delete bundle and its file associations"""
        # First delete bundle files associations
        self.db_service.execute_query(
            "DELETE FROM bundle_files WHERE bundle_id = ?",
            (bundle_id,)
        )
        # Then delete the bundle
        return self.db_service.execute_query(
            "DELETE FROM file_bundles WHERE id = ?",
            (bundle_id,)
        )
    
    # Settings operations
    def get_logo(self):
        """Get current sign in logo filename"""
        result = self.db_service.execute_query(
            "SELECT logo_filename FROM settings ORDER BY id DESC LIMIT 1",
            fetch_one=True
        )
        return result['logo_filename'] if result else None
    
    def get_header_logo(self):
        """Get current header logo filename"""
        result = self.db_service.execute_query(
            "SELECT header_logo_filename FROM settings ORDER BY id DESC LIMIT 1",
            fetch_one=True
        )
        return result['header_logo_filename'] if result else None
    
    def set_logo(self, logo_filename):
        """Set new sign in logo"""
        return self.db_service.execute_query(
            "INSERT INTO settings (logo_filename) VALUES (?)",
            (logo_filename,)
        )
    
    def set_header_logo(self, header_logo_filename):
        """Set new header logo"""
        # Get current settings
        current = self.db_service.execute_query(
            "SELECT logo_filename FROM settings ORDER BY id DESC LIMIT 1",
            fetch_one=True
        )
        
        if current:
            # Update existing record
            return self.db_service.execute_query(
                "UPDATE settings SET header_logo_filename = ? WHERE id = (SELECT MAX(id) FROM settings)",
                (header_logo_filename,)
            )
        else:
            # Create new record
            return self.db_service.execute_query(
                "INSERT INTO settings (header_logo_filename) VALUES (?)",
                (header_logo_filename,)
            )
    
    # Statistics operations
    def get_user_stats(self, user_id):
        """Get user statistics"""
        # Total files
        total_files = self.db_service.execute_query(
            "SELECT COUNT(*) as count FROM files WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )['count']
        
        # Public files
        public_files = self.db_service.execute_query(
            "SELECT COUNT(*) as count FROM files WHERE user_id = ? AND is_public = 1",
            (user_id,),
            fetch_one=True
        )['count']
        
        # Total size
        result = self.db_service.execute_query(
            "SELECT SUM(file_size) as total_size FROM files WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        total_size = result['total_size'] if result['total_size'] else 0
        
        # Total downloads
        result = self.db_service.execute_query(
            "SELECT SUM(download_count) as total_downloads FROM files WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        total_downloads = result['total_downloads'] if result['total_downloads'] else 0
        
        return {
            'total_files': total_files,
            'public_files': public_files,
            'private_files': total_files - public_files,
            'total_size': total_size,
            'total_downloads': total_downloads
        }
    
    # Password operations
    def update_user_password(self, user_id, password_hash):
        """Update user password"""
        return self.db_service.execute_query(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
    
    def get_user_password_hash(self, user_id):
        """Get user password hash"""
        result = self.db_service.execute_query(
            "SELECT password_hash FROM users WHERE id = ?",
            (user_id,),
            fetch_one=True
        )
        return result['password_hash'] if result else None

# Global database instance
db = DatabaseWrapper()