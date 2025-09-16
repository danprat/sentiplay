from google_play_scraper import reviews, Sort, app as gplay_app
import sqlite3
import re
from html import unescape
from typing import List, Dict, Tuple, Optional
from database import DatabaseManager

class PlayStoreScraper:
    """Class to handle scraping of Google Play Store reviews"""
    
    def __init__(self, database_path: str = 'data/reviews.db'):
        """
        Initialize the scraper with database path
        
        Args:
            database_path (str): Path to SQLite database file
        """
        self.database_path = database_path
        self.db_manager = DatabaseManager(database_path)
    
    def scrape_reviews(self, app_id: str, lang: str = 'en', country: str = 'us',
                      sort: Sort = Sort.NEWEST, count: int = 100,
                      filter_score_with: Optional[int] = None) -> Tuple[List[Dict], int]:
        """
        Scrape reviews from Google Play Store
        
        Args:
            app_id (str): Application ID on Google Play Store
            lang (str): Language code (default: 'en')
            country (str): Country code (default: 'us')
            sort (Sort): Sort order (default: Sort.NEWEST)
            count (int): Number of reviews to fetch (default: 100)
            filter_score_with (int, optional): Filter by score (1-5)
            
        Returns:
            Tuple[List[Dict], int]: List of reviews and session ID
        """
        # Get reviews using google-play-scraper
        result, _ = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=sort,
            count=count,
            filter_score_with=filter_score_with
        )
        
        return result, len(result)

    def get_app_details(self, app_id: str, lang: str = 'en', country: str = 'us') -> Optional[Dict[str, Optional[str]]]:
        """Fetch metadata for an app from Google Play."""
        try:
            metadata = gplay_app(app_id, lang=lang, country=country)
        except Exception as exc:  # pragma: no cover - network errors shouldn't break scraping
            print(f"Unable to fetch app metadata for {app_id}: {exc}")
            return None

        raw_description = metadata.get('shortDescription') or metadata.get('summary') or metadata.get('description') or ''
        if not raw_description and metadata.get('descriptionHTML'):
            raw_description = metadata.get('descriptionHTML')

        # Strip HTML tags and unescape entities
        clean_description = unescape(re.sub(r'<[^>]+>', ' ', raw_description or '')).strip()
        if len(clean_description) > 1200:
            clean_description = clean_description[:1197] + '...'

        categories = metadata.get('categories') or metadata.get('category') or metadata.get('genre')
        if isinstance(categories, (list, tuple)):
            category_names = []
            for cat in categories:
                if cat:
                    if isinstance(cat, dict) and 'name' in cat:
                        category_names.append(cat['name'])
                    else:
                        category_names.append(str(cat))
            categories = ', '.join(category_names)

        return {
            'title': metadata.get('title'),
            'description': clean_description,
            'genre': metadata.get('genre') or metadata.get('category'),
            'genre_id': metadata.get('genreId') or metadata.get('categoryId'),
            'categories': categories,
            'version': metadata.get('version')
        }
    
    def _create_scraping_session(self, app_id: str, lang: str, country: str, 
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
    
    def _update_session_status(self, session_id: int, status: str):
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
    
    def _save_reviews(self, reviews_data: List[Dict], app_id: str, lang: str, country: str) -> int:
        """
        Save reviews to database
        
        Args:
            reviews_data (List[Dict]): List of review dictionaries
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
                    (app_id, review_id, user_name, user_image, content, score, 
                     thumbs_up_count, review_created_version, at, reply_content, 
                     replied_at, lang, country)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
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
    
    def save_reviews_to_db(self, reviews_data: List[Dict], session_id: int, app_id: str, lang: str, country: str) -> int:
        """
        Save reviews to database using DatabaseManager
        
        Args:
            reviews_data (List[Dict]): List of review dictionaries
            session_id (int): Session ID
            app_id (str): Application ID
            lang (str): Language code
            country (str): Country code
            
        Returns:
            int: Number of reviews saved
        """
        return self.db_manager.save_reviews(reviews_data, app_id, lang, country)
    
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
            WHERE app_id = ? AND lang = ? AND country = ?
        ''', (session['app_id'], session['lang'], session['country']))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
