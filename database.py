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
                status TEXT
            )
        ''')
        
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