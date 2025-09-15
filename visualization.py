import sqlite3
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud
from io import BytesIO
from typing import Optional, Dict, List, Tuple
import base64
from database import DatabaseManager

class DataVisualizer:
    """Class to handle data visualization including wordclouds and charts"""
    
    def __init__(self, database_path: str = 'data/reviews.db'):
        """
        Initialize the visualizer with database path
        
        Args:
            database_path (str): Path to SQLite database file
        """
        self.database_path = database_path
        self.db_manager = DatabaseManager(database_path)
        # Set up matplotlib style - use a simple style that's available
        try:
            plt.style.use('seaborn-v0_8')
        except:
            try:
                plt.style.use('seaborn')
            except:
                pass  # Use default style
    
    def generate_wordcloud(self, session_id: int, width: int = 800, height: int = 400) -> Optional[bytes]:
        """
        Generate wordcloud from processed reviews for a session
        
        Args:
            session_id (int): Session ID
            width (int): Width of wordcloud image
            height (int): Height of wordcloud image
            
        Returns:
            Optional[bytes]: Wordcloud image as bytes or None if failed
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
            return None
        
        app_id, lang, country = session_row
        
        # Get all processed reviews for this session
        cursor.execute('''
            SELECT stemmed_content FROM processed_reviews 
            WHERE review_id IN (
                SELECT review_id FROM raw_reviews 
                WHERE session_id = ?
            )
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # Combine all processed text
        all_text = ' '.join([row[0] for row in rows if row[0]])
        
        if not all_text.strip():
            return None
        
        # Generate wordcloud
        try:
            wordcloud = WordCloud(
                width=width,
                height=height,
                background_color='white',
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                random_state=42
            ).generate(all_text)
            
            # Create image
            plt.figure(figsize=(width/100, height/100))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            
            # Save to bytes
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', pad_inches=0)
            plt.close()
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"Error generating wordcloud: {e}")
            return None
    
    def generate_rating_chart(self, session_id: int) -> Optional[bytes]:
        """
        Generate rating distribution chart for a session
        
        Args:
            session_id (int): Session ID
            
        Returns:
            Optional[bytes]: Chart image as bytes or None if failed
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
            return None
        
        app_id, lang, country = session_row
        
        # Get rating distribution
        cursor.execute('''
            SELECT score, COUNT(*) as count FROM raw_reviews 
            WHERE session_id = ?
            GROUP BY score
            ORDER BY score
        ''', (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # Prepare data for chart
        scores = [row[0] for row in rows]
        counts = [row[1] for row in rows]
        
        # Create bar chart
        try:
            plt.figure(figsize=(10, 6))
            bars = plt.bar(scores, counts, color=['#ff9999','#66b3ff','#99ff99','#ffcc99','#ff99cc'])
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
            
            plt.xlabel('Rating')
            plt.ylabel('Number of Reviews')
            plt.title('Rating Distribution')
            plt.xticks(scores)
            plt.grid(axis='y', alpha=0.3)
            
            # Save to bytes
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            plt.close()
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"Error generating rating chart: {e}")
            return None
    
    def get_statistics(self, session_id: int) -> Optional[Dict]:
        """
        Get statistics for a session
        
        Args:
            session_id (int): Session ID
            
        Returns:
            Optional[Dict]: Statistics data or None if failed
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
            return None
        
        app_id, lang, country = session_row
        
        # Get statistics
        stats = {}
        
        # Total reviews
        cursor.execute('''
            SELECT COUNT(*) FROM raw_reviews 
            WHERE session_id = ?
        ''', (session_id,))
        stats['total_reviews'] = cursor.fetchone()[0]
        
        # Average rating
        cursor.execute('''
            SELECT AVG(score) FROM raw_reviews 
            WHERE session_id = ?
        ''', (session_id,))
        avg_rating = cursor.fetchone()[0]
        stats['average_rating'] = round(avg_rating, 2) if avg_rating else 0
        
        # Rating distribution
        cursor.execute('''
            SELECT score, COUNT(*) as count FROM raw_reviews 
            WHERE session_id = ?
            GROUP BY score
            ORDER BY score
        ''', (session_id,))
        
        rating_dist = {}
        for score, count in cursor.fetchall():
            rating_dist[score] = count
        stats['rating_distribution'] = rating_dist
        
        # Most common words (from processed reviews)
        cursor.execute('''
            SELECT stemmed_content FROM processed_reviews 
            WHERE review_id IN (
                SELECT review_id FROM raw_reviews 
                WHERE session_id = ?
            )
        ''', (session_id,))
        
        rows = cursor.fetchall()
        all_text = ' '.join([row[0] for row in rows if row[0]])
        
        # Simple word frequency (top 5)
        if all_text:
            words = all_text.split()
            word_freq = {}
            for word in words:
                if len(word) > 2:  # Only count words with more than 2 characters
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            stats['most_common_words'] = dict(sorted_words[:5])
        else:
            stats['most_common_words'] = {}
        
        conn.close()
        
        return stats
    
    def get_reviews_data(self, session_id: int, page: int = 1, limit: int = 20) -> Optional[Dict]:
        """
        Get paginated reviews data for a session
        
        Args:
            session_id (int): Session ID
            page (int): Page number (default: 1)
            limit (int): Number of reviews per page (default: 20)
            
        Returns:
            Optional[Dict]: Reviews data with pagination or None if failed
        """
        # Get session information
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT app_id, lang, country FROM scraping_sessions WHERE id = ?
        ''', (session_id,))
        
        session_row = cursor.fetchone()
        if not session_row:
            conn.close()
            return None
        
        app_id, lang, country = session_row
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count
        cursor.execute('''
            SELECT COUNT(*) FROM raw_reviews 
            WHERE session_id = ?
        ''', (session_id,))
        total = cursor.fetchone()[0]
        
        # Get reviews for this page
        cursor.execute('''
            SELECT review_id, user_name, content, score, at FROM raw_reviews 
            WHERE session_id = ?
            ORDER BY at DESC
            LIMIT ? OFFSET ?
        ''', (session_id, limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        reviews = [dict(row) for row in rows]
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        
        return {
            'reviews': reviews,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }