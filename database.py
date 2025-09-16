import sqlite3
import os
from typing import Optional, Dict, List, Tuple

class DatabaseManager:
    """Class to handle database operations"""
    
    def __init__(self, database_path: str = 'data/reviews.db'):
        """
        Initialize the database manager
        
        Args:
            database_path (str): Path to SQLite database file
        """
        self.database_path = database_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create raw_reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_reviews (
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
        
        # Create processed_reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT UNIQUE,
                original_content TEXT,
                cleaned_content TEXT,
                stopwords_removed TEXT,
                stemmed_content TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (review_id) REFERENCES raw_reviews (review_id)
            )
        ''')
        
        # Create scraping_sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT NOT NULL,
                lang TEXT,
                country TEXT,
                filter_score INTEGER,
                count INTEGER,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                finished_at DATETIME,
                status TEXT,
                app_title TEXT,
                app_description TEXT,
                app_genre TEXT,
                app_genre_id TEXT,
                app_categories TEXT,
                app_version TEXT
            )
        ''')

        # Ensure metadata columns exist for older databases
        cursor.execute("PRAGMA table_info(scraping_sessions)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        metadata_columns = {
            'app_title': 'TEXT',
            'app_description': 'TEXT',
            'app_genre': 'TEXT',
            'app_genre_id': 'TEXT',
            'app_categories': 'TEXT',
            'app_version': 'TEXT'
        }

        for column_name, column_type in metadata_columns.items():
            if column_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE scraping_sessions ADD COLUMN {column_name} {column_type}"
                )
        
        conn.commit()
        conn.close()
    
    def create_scraping_session(self, app_id: str, lang: str, country: str, 
                               filter_score: Optional[int], count: int) -> int:
        """
        Create a scraping session record in database
        
        Returns:
            int: Session ID
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scraping_sessions 
            (app_id, lang, country, filter_score, count, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (app_id, lang, country, filter_score, count, 'initialized'))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def update_session_status(self, session_id: int, status: str):
        """
        Update scraping session status
        
        Args:
            session_id (int): Session ID
            status (str): New status
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        if status == 'completed':
            cursor.execute('''
                UPDATE scraping_sessions 
                SET status = ?, finished_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, session_id))
        else:
            cursor.execute('''
                UPDATE scraping_sessions 
                SET status = ?
                WHERE id = ?
            ''', (status, session_id))
        
        conn.commit()
        conn.close()

    def get_session_status(self, session_id: int) -> Optional[Dict]:
        """
        Get scraping session status
        
        Args:
            session_id (int): Session ID
            
        Returns:
            Optional[Dict]: Session data or None if not found
        """
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM scraping_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None

    def update_session_app_info(self, session_id: int, app_info: Dict[str, Optional[str]]):
        """Persist Google Play metadata for a scraping session."""
        if not app_info:
            return

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        fields = {
            'app_title': app_info.get('title'),
            'app_description': app_info.get('description'),
            'app_genre': app_info.get('genre'),
            'app_genre_id': app_info.get('genre_id'),
            'app_version': app_info.get('version')
        }

        # Filter out None-only updates to avoid empty SET clause
        updates = {key: value for key, value in fields.items() if value is not None}
        if not updates:
            conn.close()
            return

        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        params = list(updates.values()) + [session_id]

        cursor.execute(
            f"UPDATE scraping_sessions SET {set_clause} WHERE id = ?",
            params
        )

        conn.commit()
        conn.close()

    def save_reviews(self, reviews_data: List[Dict], session_id: int, app_id: str, lang: str, country: str) -> int:
        """
        Save reviews to database
        
        Args:
            reviews_data (List[Dict]): List of review dictionaries
            session_id (int): Session ID
            app_id (str): Application ID
            lang (str): Language code
            country (str): Country code
            
        Returns:
            int: Number of reviews saved
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for review in reviews_data:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO raw_reviews 
                    (session_id, app_id, review_id, user_name, user_image, content, score, 
                     thumbs_up_count, review_created_version, at, reply_content, 
                     replied_at, lang, country)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    app_id,
                    review.get('reviewId'),
                    review.get('userName'),
                    review.get('userImage'),
                    review.get('content'),
                    review.get('score'),
                    review.get('thumbsUpCount'),
                    review.get('reviewCreatedVersion'),
                    review.get('at'),
                    review.get('replyContent'),
                    review.get('repliedAt'),
                    lang,
                    country
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                    
            except sqlite3.Error as e:
                print(f"Error saving review {review.get('reviewId')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return saved_count
    
    def get_reviews_count(self, session_id: int) -> int:
        """
        Get count of reviews for a session
        
        Args:
            session_id (int): Session ID
            
        Returns:
            int: Number of reviews
        """
        # Get app_id and other filters from session
        session = self.get_session_status(session_id)
        if not session:
            return 0
            
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM raw_reviews 
            WHERE session_id = ?
        ''', (session_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def check_existing_data(self, app_id: str, lang: str, country: str, count: int) -> Optional[int]:
        """
        Check if there's existing data for the same parameters
        
        Args:
            app_id (str): Application ID
            lang (str): Language code
            country (str): Country code
            count (int): Requested review count
            
        Returns:
            Optional[int]: Existing session_id if found, None otherwise
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Look for completed sessions with same parameters and sufficient data
        cursor.execute('''
            SELECT s.id, COUNT(r.id) as review_count
            FROM scraping_sessions s
            LEFT JOIN raw_reviews r ON s.id = r.session_id
            WHERE s.app_id = ? AND s.lang = ? AND s.country = ? 
            AND s.status = 'completed'
            AND s.started_at > datetime('now', '-7 days')
            GROUP BY s.id
            HAVING review_count >= ?
            ORDER BY s.started_at DESC
            LIMIT 1
        ''', (app_id, lang, country, count))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    
    def get_processed_reviews_count(self, session_id: int) -> int:
        """
        Get count of processed reviews for a session
        
        Args:
            session_id (int): Session ID
            
        Returns:
            int: Number of processed reviews
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM processed_reviews 
            WHERE review_id IN (
                SELECT review_id FROM raw_reviews 
                WHERE session_id = ?
            )
        ''', (session_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def save_preprocessing_result(self, review_id: str, result: Dict[str, str]) -> bool:
        """
        Save preprocessing result to database
        
        Args:
            review_id (str): Review ID
            result (Dict[str, str]): Preprocessing result
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO processed_reviews 
                (review_id, original_content, cleaned_content, stopwords_removed, stemmed_content)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                review_id,
                result['original'],
                result['cleaned'],
                result['stopwords_removed'],
                result['stemmed']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"Error saving preprocessing result for review {review_id}: {e}")
            return False
    
    def get_processed_review(self, review_id: str) -> Optional[Dict]:
        """
        Get processed review data
        
        Args:
            review_id (str): Review ID
            
        Returns:
            Optional[Dict]: Processed review data or None if not found
        """
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM processed_reviews WHERE review_id = ?
        ''', (review_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def cleanup_old_data(self, keep_days: int = 7, keep_sessions: int = 10):
        """
        Clean up old data to prevent database from getting too large
        
        Args:
            keep_days (int): Keep data from last N days (default: 7)
            keep_sessions (int): Always keep at least N most recent sessions (default: 10)
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, started_at FROM scraping_sessions 
                ORDER BY started_at DESC
            ''')
            sessions = cursor.fetchall()

            if not sessions:
                conn.close()
                return 0

            # Determine sessions to keep (latest keep_sessions)
            sessions_to_keep = {row[0] for row in sessions[:keep_sessions]}

            # Determine sessions old by date threshold if requested
            old_by_age = set()
            if keep_days is not None:
                cursor.execute(
                    '''SELECT id FROM scraping_sessions WHERE started_at < datetime('now', ?)''',
                    (f'-{keep_days} days',)
                )
                old_by_age = {row[0] for row in cursor.fetchall()}

            # Combine any session beyond keep limit or older than threshold
            sessions_to_delete = []
            for session_id, _ in sessions:
                if session_id not in sessions_to_keep or session_id in old_by_age:
                    sessions_to_delete.append(session_id)

            if not sessions_to_delete:
                print("No old sessions to delete")
                conn.close()
                return 0

            deleted_count = 0

            # Delete data for each session
            for session_id in sessions_to_delete:
                # Delete processed reviews first (foreign key constraint)
                cursor.execute('''
                    DELETE FROM processed_reviews 
                    WHERE review_id IN (
                        SELECT review_id FROM raw_reviews WHERE session_id = ?
                    )
                ''', (session_id,))

                # Delete raw reviews
                cursor.execute('DELETE FROM raw_reviews WHERE session_id = ?', (session_id,))

                # Delete session
                cursor.execute('DELETE FROM scraping_sessions WHERE id = ?', (session_id,))

                deleted_count += 1

            conn.commit()
            conn.close()

            # Vacuum in a new connection so the deleted pages are released immediately
            try:
                with sqlite3.connect(self.database_path, isolation_level=None) as vacuum_conn:
                    vacuum_cursor = vacuum_conn.cursor()
                    # Reduce the size of any leftover WAL file before vacuuming
                    vacuum_cursor.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                    vacuum_cursor.fetchone()
                    vacuum_cursor.execute('VACUUM')
            except sqlite3.Error as vacuum_error:
                print(f"Cleanup completed but VACUUM failed: {vacuum_error}")

            print(f"Deleted {deleted_count} old sessions to free up database space")
            return deleted_count

        except sqlite3.Error as e:
            print(f"Error during cleanup: {e}")
            return 0
