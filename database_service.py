#!/usr/bin/env python3
"""
Database Service for EY File Sharing Application
Handles all database operations, migrations, and schema management
"""
import os
import sqlite3
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path=None):
        if db_path is None:
            # Get the directory where this script is located
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, 'file_sharing.db')
        self.db_path = db_path
        self.schema_version = 3  # Current schema version
        
    def get_connection(self):
        """Get database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def execute_query(self, query, params=None, fetch=False, fetch_one=False):
        """Execute a query safely with connection management"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch:
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def table_exists(self, table_name):
        """Check if a table exists"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result is not None
    
    def get_schema_version(self):
        """Get current schema version from database"""
        try:
            if not self.table_exists('schema_version'):
                return 0
            
            result = self.execute_query(
                "SELECT version FROM schema_version ORDER BY id DESC LIMIT 1",
                fetch_one=True
            )
            return result['version'] if result else 0
        except:
            return 0
    
    def set_schema_version(self, version):
        """Set schema version in database"""
        if not self.table_exists('schema_version'):
            self.execute_query('''
                CREATE TABLE schema_version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        self.execute_query(
            "INSERT INTO schema_version (version) VALUES (?)",
            (version,)
        )
    
    def create_initial_schema(self):
        """Create initial database schema (version 1)"""
        logger.info("Creating initial database schema...")
        
        # Users table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("✓ Users table created")
        
        # Files table (initial version)
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                is_public BOOLEAN DEFAULT 0,
                share_token TEXT UNIQUE,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                file_type TEXT,
                download_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        logger.info("✓ Files table created")
        
        # Settings table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logo_filename TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("✓ Settings table created")
        
        self.set_schema_version(1)
        logger.info("✓ Schema version 1 applied")
    
    def migrate_to_version_2(self):
        """Add transaction_number field to files table"""
        logger.info("Migrating to schema version 2...")
        
        try:
            # Check if column already exists
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(files)")
            columns = [column[1] for column in cursor.fetchall()]
            conn.close()
            
            if 'transaction_number' not in columns:
                self.execute_query('''
                    ALTER TABLE files ADD COLUMN transaction_number TEXT
                ''')
                logger.info("✓ Added transaction_number column to files table")
            else:
                logger.info("✓ transaction_number column already exists")
            
            self.set_schema_version(2)
            logger.info("✓ Schema version 2 applied")
        except Exception as e:
            logger.error(f"Error migrating to version 2: {e}")
            raise
    
    def migrate_to_version_3(self):
        """Add file bundles functionality"""
        logger.info("Migrating to schema version 3...")
        
        # File bundles table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS file_bundles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bundle_name TEXT NOT NULL,
                transaction_number TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                is_public BOOLEAN DEFAULT 0,
                share_token TEXT UNIQUE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        logger.info("✓ File bundles table created")
        
        # Bundle files relationship table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS bundle_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bundle_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                FOREIGN KEY (bundle_id) REFERENCES file_bundles (id),
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')
        logger.info("✓ Bundle files relationship table created")
        
        self.set_schema_version(3)
        logger.info("✓ Schema version 3 applied")
    
    def run_migrations(self):
        """Run all necessary migrations"""
        current_version = self.get_schema_version()
        target_version = self.schema_version
        
        logger.info(f"Current schema version: {current_version}")
        logger.info(f"Target schema version: {target_version}")
        
        if current_version == target_version:
            logger.info("Database is up to date")
            return
        
        if current_version == 0:
            self.create_initial_schema()
            current_version = 1
        
        if current_version < 2:
            self.migrate_to_version_2()
            current_version = 2
        
        if current_version < 3:
            self.migrate_to_version_3()
            current_version = 3
        
        logger.info(f"Database migration completed. Current version: {current_version}")
    
    def initialize_database(self):
        """Initialize database with schema and run migrations"""
        logger.info("Initializing database...")
        
        # Ensure database file exists
        if not os.path.exists(self.db_path):
            logger.info(f"Creating new database: {self.db_path}")
        
        # Run migrations
        self.run_migrations()
        
        # Verify all tables exist
        required_tables = ['users', 'files', 'settings', 'file_bundles', 'bundle_files', 'schema_version']
        missing_tables = []
        
        for table in required_tables:
            if not self.table_exists(table):
                missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"Missing tables after initialization: {missing_tables}")
            raise Exception(f"Database initialization failed. Missing tables: {missing_tables}")
        
        logger.info("✅ Database initialization completed successfully")
    
    def reset_database(self):
        """Reset database completely (DEVELOPMENT ONLY)"""
        logger.warning("RESETTING DATABASE - ALL DATA WILL BE LOST")
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logger.info("Previous database deleted")
        
        self.initialize_database()
        logger.info("Database reset completed")
    
    def get_database_info(self):
        """Get database information for debugging"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            info = {
                'database_path': os.path.abspath(self.db_path),
                'database_exists': os.path.exists(self.db_path),
                'schema_version': self.get_schema_version(),
                'tables': tables
            }
            
            # Get table info for each table
            table_info = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                table_info[table] = [
                    {
                        'name': col[1],
                        'type': col[2],
                        'not_null': bool(col[3]),
                        'primary_key': bool(col[5])
                    }
                    for col in columns
                ]
            
            info['table_info'] = table_info
            conn.close()
            
            return info
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {'error': str(e)}

# Convenience functions for common operations
def get_db_service():
    """Get database service instance"""
    return DatabaseService()

def init_database():
    """Initialize database (convenience function)"""
    db_service = get_db_service()
    db_service.initialize_database()

def reset_database():
    """Reset database (convenience function for development)"""
    db_service = get_db_service()
    db_service.reset_database()

if __name__ == "__main__":
    # Command line interface for database management
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python database_service.py [init|reset|info|migrate]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    db_service = DatabaseService()
    
    if command == "init":
        db_service.initialize_database()
    elif command == "reset":
        response = input("This will delete all data. Are you sure? (yes/no): ")
        if response.lower() == 'yes':
            db_service.reset_database()
        else:
            print("Operation cancelled")
    elif command == "info":
        info = db_service.get_database_info()
        print("\n=== Database Information ===")
        for key, value in info.items():
            if key == 'table_info':
                print(f"\n{key}:")
                for table, columns in value.items():
                    print(f"  {table}:")
                    for col in columns:
                        print(f"    {col['name']} ({col['type']})")
            else:
                print(f"{key}: {value}")
    elif command == "migrate":
        db_service.run_migrations()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: init, reset, info, migrate")
        sys.exit(1)