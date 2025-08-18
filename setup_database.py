#!/usr/bin/env python3
"""
Database Setup Script for EY File Sharing Application
Run this script to initialize or update the database
"""
import os
import sys
from database_service import DatabaseService

def main():
    print("🔧 EY File Sharing Database Setup")
    print("=" * 40)
    
    # Create database service
    db_service = DatabaseService()
    
    try:
        # Get current database info
        print("📊 Checking current database status...")
        
        db_exists = os.path.exists(db_service.db_path)
        current_version = db_service.get_schema_version() if db_exists else 0
        target_version = db_service.schema_version
        
        print(f"Database file: {os.path.abspath(db_service.db_path)}")
        print(f"Database exists: {'Yes' if db_exists else 'No'}")
        print(f"Current schema version: {current_version}")
        print(f"Target schema version: {target_version}")
        print()
        
        if current_version == target_version and db_exists:
            print("✅ Database is already up to date!")
            
            # Verify all tables exist
            required_tables = ['users', 'files', 'settings', 'file_bundles', 'bundle_files']
            missing_tables = []
            
            for table in required_tables:
                if not db_service.table_exists(table):
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"⚠️ Missing tables detected: {missing_tables}")
                print("🔄 Running repair...")
                db_service.initialize_database()
                print("✅ Database repaired successfully!")
            else:
                print("🔍 All tables verified and present.")
        
        else:
            if current_version == 0:
                print("🆕 Creating new database...")
            else:
                print(f"🔄 Upgrading database from version {current_version} to {target_version}...")
            
            # Initialize/migrate database
            db_service.initialize_database()
            print("✅ Database setup completed successfully!")
        
        # Show final database info
        print("\n📋 Final Database Status:")
        info = db_service.get_database_info()
        print(f"Schema version: {info['schema_version']}")
        print(f"Tables: {', '.join(info['tables'])}")
        
        print("\n🎉 Database is ready for use!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check file permissions")
        print("2. Ensure Python has write access to the directory")
        print("3. Try running as administrator (if on Windows)")
        print("4. Check if database file is locked by another process")
        sys.exit(1)

if __name__ == "__main__":
    main()