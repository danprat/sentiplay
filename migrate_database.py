#!/usr/bin/env python3
"""
Database migration script to add session_id to existing reviews
"""

import sqlite3
import os

def migrate_database():
    """Migrate existing database to new structure"""
    
    db_path = 'data/reviews.db'
    
    # Backup original database
    backup_path = 'data/reviews_backup.db'
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if session_id column exists
        cursor.execute("PRAGMA table_info(raw_reviews)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'session_id' not in columns:
            print("Adding session_id column to raw_reviews table...")
            
            # Add session_id column
            cursor.execute('ALTER TABLE raw_reviews ADD COLUMN session_id INTEGER')
            
            # Update existing reviews with session_id = 1 (default session)
            cursor.execute('UPDATE raw_reviews SET session_id = 1 WHERE session_id IS NULL')
            
            print("Migration completed successfully!")
        else:
            print("Database already has session_id column.")
        
        # Create new table structure if needed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_reviews_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                app_id TEXT NOT NULL,
                review_id TEXT,
                user_name TEXT,
                user_image TEXT,
                content TEXT,
                score INTEGER,
                thumbs_up_count INTEGER,
                review_created_version TEXT,
                at DATETIME,
                reply_content TEXT,
                replied_at DATETIME,
                lang TEXT,
                country TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES scraping_sessions (id),
                UNIQUE(session_id, review_id)
            )
        ''')
        
        # Check if we need to migrate data to new structure
        cursor.execute("SELECT COUNT(*) FROM raw_reviews_new")
        new_table_count = cursor.fetchone()[0]
        
        if new_table_count == 0:
            print("Migrating data to new table structure...")
            
            cursor.execute('''
                INSERT OR IGNORE INTO raw_reviews_new 
                SELECT * FROM raw_reviews
            ''')
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE raw_reviews')
            cursor.execute('ALTER TABLE raw_reviews_new RENAME TO raw_reviews')
            
            print("Data migration completed!")
        
        conn.commit()
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
