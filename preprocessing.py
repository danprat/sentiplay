import re
import sqlite3
from typing import Optional, Dict
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from database import DatabaseManager

class TextPreprocessor:
    """Class to handle text preprocessing for Indonesian language"""
    
    def __init__(self, database_path: str = 'data/reviews.db'):
        """
        Initialize the preprocessor with database path and NLP tools
        
        Args:
            database_path (str): Path to SQLite database file
        """
        self.database_path = database_path
        self.db_manager = DatabaseManager(database_path)
        
        # Initialize Sastrawi stopword remover
        stopword_factory = StopWordRemoverFactory()
        self.stopword_remover = stopword_factory.create_stop_word_remover()
        
        # Initialize Sastrawi stemmer
        stemmer_factory = StemmerFactory()
        self.stemmer = stemmer_factory.create_stemmer()
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing URLs, mentions, hashtags, and special characters
        
        Args:
            text (str): Input text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove mentions and hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
    
    def remove_stopwords(self, text: str) -> str:
        """
        Remove Indonesian stopwords from text
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text without stopwords
        """
        if not text:
            return ""
        
        return self.stopword_remover.remove(text)
    
    def stem_text(self, text: str) -> str:
        """
        Stem Indonesian text to its root words
        
        Args:
            text (str): Input text
            
        Returns:
            str: Stemmed text
        """
        if not text:
            return ""
        
        return self.stemmer.stem(text)
    
    def preprocess_text(self, text: str) -> Dict[str, str]:
        """
        Complete text preprocessing pipeline
        
        Args:
            text (str): Input text
            
        Returns:
            Dict[str, str]: Dictionary with preprocessing steps
        """
        if not text:
            return {
                'original': '',
                'cleaned': '',
                'stopwords_removed': '',
                'stemmed': ''
            }
        
        # Step 1: Clean text
        cleaned_text = self.clean_text(text)
        
        # Step 2: Remove stopwords
        stopwords_removed = self.remove_stopwords(cleaned_text)
        
        # Step 3: Stem text
        stemmed_text = self.stem_text(stopwords_removed)
        
        return {
            'original': text,
            'cleaned': cleaned_text,
            'stopwords_removed': stopwords_removed,
            'stemmed': stemmed_text
        }
    
    def preprocess_review(self, review_id: str) -> bool:
        """
        Preprocess a single review by ID and save to database
        
        Args:
            review_id (str): Review ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get review content from database
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content FROM raw_reviews WHERE review_id = ?
        ''', (review_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False
        
        content = row['content']
        
        # Preprocess text
        preprocessing_result = self.preprocess_text(content)
        
        # Save preprocessing result to database
        return self._save_preprocessing_result(review_id, preprocessing_result)
    
    def preprocess_all_reviews(self, session_id: int) -> int:
        """
        Preprocess all reviews for a session
        
        Args:
            session_id (int): Session ID
            
        Returns:
            int: Number of reviews processed
        """
        # Get session information
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT app_id, lang, country FROM scraping_sessions WHERE id = ?
        ''', (session_id,))
        
        session_row = cursor.fetchone()
        if not session_row:
            conn.close()
            return 0
        
        app_id, lang, country = session_row
        
        # Get all reviews for this session
        cursor.execute('''
            SELECT review_id, content FROM raw_reviews 
            WHERE session_id = ?
        ''', (session_id,))
        
        reviews = cursor.fetchall()
        conn.close()
        
        processed_count = 0
        
        for review_id, content in reviews:
            preprocessing_result = self.preprocess_text(content)
            if self._save_preprocessing_result(review_id, preprocessing_result):
                processed_count += 1
        
        return processed_count
    
    def _save_preprocessing_result(self, review_id: str, result: Dict[str, str]) -> bool:
        """
        Save preprocessing result to database using DatabaseManager
        
        Args:
            review_id (str): Review ID
            result (Dict[str, str]): Preprocessing result
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.db_manager.save_preprocessing_result(review_id, result)
    
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