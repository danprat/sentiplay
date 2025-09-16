from flask import Flask, render_template, request, jsonify, send_file, Response
import os
import sqlite3
from dotenv import load_dotenv
import json
import threading
import csv
from io import BytesIO, StringIO
from scraper import PlayStoreScraper
from preprocessing import TextPreprocessor
from visualization import DataVisualizer
from database import DatabaseManager

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Initialize components
db_manager = DatabaseManager()
scraper = PlayStoreScraper()
preprocessor = TextPreprocessor()
visualizer = DataVisualizer()

def scrape_reviews_background(session_id, app_id, lang, country, filter_score, count, sort='NEWEST'):
    """Background function to scrape reviews"""
    try:
        # Update session status to scraping
        db_manager.update_session_status(session_id, 'scraping')

        # Try to fetch metadata for the application and persist it for later display
        try:
            app_details = scraper.get_app_details(app_id=app_id, lang=lang, country=country)
            if app_details:
                db_manager.update_session_app_info(session_id, app_details)
        except Exception as metadata_error:
            print(f"Failed to store app metadata for session {session_id}: {metadata_error}")
        
        # Convert sort string to Sort enum
        from google_play_scraper import Sort
        sort_enum = Sort.NEWEST if sort == 'NEWEST' else Sort.MOST_RELEVANT
        
        # Scrape reviews
        reviews, _ = scraper.scrape_reviews(
            app_id=app_id,
            lang=lang,
            country=country,
            sort=sort_enum,
            filter_score_with=filter_score,
            count=count
        )
        
        # Save reviews to database
        saved_count = db_manager.save_reviews(reviews, session_id, app_id, lang, country)
        print(f"Saved {saved_count} reviews for session {session_id}")
        
        if saved_count == 0:
            print(f"No reviews saved for session {session_id}")
            db_manager.update_session_status(session_id, 'failed')
            return
        
        # Update session status to processing
        db_manager.update_session_status(session_id, 'processing')
        
        # Preprocess reviews
        processed_count = preprocessor.preprocess_all_reviews(session_id)
        print(f"Processed {processed_count} out of {saved_count} reviews for session {session_id}")
        
        # Always update to completed if we have any data, even if processing failed partially
        if saved_count > 0:
            db_manager.update_session_status(session_id, 'completed')
            print(f"Scraping completed for session {session_id}. Saved {saved_count} reviews, processed {processed_count} reviews.")
        else:
            print(f"No reviews saved for session {session_id}")
            db_manager.update_session_status(session_id, 'failed')
        
    except Exception as e:
        print(f"Error in scraping background task for session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        db_manager.update_session_status(session_id, 'failed')

# Routes
@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for Docker/Kubernetes"""
    return jsonify({"status": "healthy", "service": "sentiplay"}), 200

@app.route('/api/scrape', methods=['POST'])
def scrape_reviews():
    """API endpoint to start scraping reviews"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Extract parameters
        app_id = data.get('app_id')
        lang = data.get('lang', 'en')
        country = data.get('country', 'us')
        filter_score = data.get('filter_score')
        count = data.get('count', 100)
        sort = data.get('sort', 'NEWEST')
        force_new = data.get('force_new', False)  # Option to force new scraping
        
        # Validate required parameters
        if not app_id:
            return jsonify({"error": "App ID is required"}), 400
        
        # Disable caching - always scrape fresh data
        # This ensures Analysis Results are always up-to-date and don't use old cached data
        print(f"Starting fresh scraping for app_id: {app_id}, filter_score: {filter_score}")
        
        # Clean up old data to prevent database from growing too large
        cleanup_count = db_manager.cleanup_old_data(keep_days=3, keep_sessions=5)
        if cleanup_count > 0:
            print(f"Cleaned up {cleanup_count} old sessions")
        
        # Create new scraping session
        session_id = db_manager.create_scraping_session(
            app_id=app_id,
            lang=lang,
            country=country,
            filter_score=filter_score,
            count=count
        )
        
        # Start background scraping task
        thread = threading.Thread(
            target=scrape_reviews_background,
            args=(session_id, app_id, lang, country, filter_score, count, sort)
        )
        thread.start()
        
        return jsonify({
            "session_id": session_id,
            "status": "started",
            "message": "Scraping started successfully",
            "cached": False
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scrape/status/<int:session_id>')
def scrape_status(session_id):
    """API endpoint to check scraping status"""
    try:
        session_data = db_manager.get_session_status(session_id)
        
        if not session_data:
            return jsonify({"error": "Session not found"}), 404
            
        # Get review count
        review_count = db_manager.get_reviews_count(session_id)
        processed_count = db_manager.get_processed_reviews_count(session_id)
        
        return jsonify({
            "session_id": session_id,
            "status": session_data["status"],
            "review_count": review_count,
            "processed_count": processed_count,
            "app_id": session_data["app_id"],
            "lang": session_data["lang"],
            "country": session_data["country"]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wordcloud/<int:session_id>')
def wordcloud_image(session_id):
    """API endpoint to get wordcloud image"""
    try:
        # Generate wordcloud
        wordcloud_bytes = visualizer.generate_wordcloud(session_id)
        
        if not wordcloud_bytes:
            return jsonify({"error": "Failed to generate wordcloud"}), 500
        
        # Return image
        return send_file(
            BytesIO(wordcloud_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'wordcloud_{session_id}.png'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rating-chart/<int:session_id>')
def rating_chart(session_id):
    """API endpoint to get rating chart image"""
    try:
        # Generate rating chart
        chart_bytes = visualizer.generate_rating_chart(session_id)
        
        if not chart_bytes:
            return jsonify({"error": "Failed to generate rating chart"}), 500
        
        # Return image
        return send_file(
            BytesIO(chart_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'rating_chart_{session_id}.png'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/statistics/<int:session_id>')
def statistics(session_id):
    """API endpoint to get statistics"""
    try:
        # Get statistics
        stats = visualizer.get_statistics(session_id)
        
        if not stats:
            return jsonify({"error": "Failed to get statistics"}), 500
            
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<int:session_id>')
def reviews_data(session_id):
    """API endpoint to get reviews data"""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Get reviews data
        reviews = visualizer.get_reviews_data(session_id, page, limit)
        
        if not reviews:
            return jsonify({"error": "Failed to get reviews data"}), 500
            
        return jsonify(reviews)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/reviews/<int:session_id>')
def download_reviews_csv(session_id):
    """API endpoint to download reviews as CSV"""
    try:
        # Get all reviews for the session (no pagination)
        reviews_data = visualizer.get_all_reviews_for_download(session_id)
        
        if not reviews_data:
            return jsonify({"error": "No reviews found for this session"}), 404
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write CSV header
        writer.writerow([
            'Session ID', 'App ID', 'Review ID', 'User Name', 'Rating', 
            'Date', 'Content', 'Original Content', 'Cleaned Content', 
            'Processed Content', 'Thumbs Up'
        ])
        
        # Write reviews data
        for review in reviews_data:
            writer.writerow([
                review.get('session_id', ''),
                review.get('app_id', ''),
                review.get('review_id', ''),
                review.get('user_name', ''),
                review.get('score', ''),
                review.get('at', ''),
                review.get('content', ''),
                review.get('original_content', ''),
                review.get('cleaned_content', ''),
                review.get('stemmed_content', ''),
                review.get('thumbs_up_count', '')
            ])
        
        # Prepare response
        output.seek(0)
        
        # Get session info for filename
        session_info = db_manager.get_session_status(session_id)
        app_id = session_info.get('app_id', 'unknown') if session_info else 'unknown'
        filename = f"reviews_{app_id}_{session_id}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    import sys
    
    # Parse command line arguments for Docker
    host = '127.0.0.1'
    port = 5000
    debug = True
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--host='):
                host = arg.split('=')[1]
            elif arg.startswith('--port='):
                port = int(arg.split('=')[1])
            elif arg == '--host':
                host = '0.0.0.0'
    
    # Check if running in production
    if os.environ.get('FLASK_ENV') == 'production':
        debug = False
        host = '0.0.0.0'
    
    print(f"Starting Sentiplay - Analisis Sentimen Akademik server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
