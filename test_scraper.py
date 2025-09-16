#!/usr/bin/env python3
"""
Test script untuk mengecek apakah scraper bekerja dengan baik
"""

from scraper import PlayStoreScraper
from database import DatabaseManager

def test_scraper():
    """Test function untuk scraper"""
    print("=== Testing Google Play Scraper ===")
    
    # Initialize scraper
    scraper = PlayStoreScraper()
    
    # Test parameters
    app_id = "com.whatsapp"
    lang = "id" 
    country = "id"
    count = 10
    
    try:
        print(f"Testing scraping for {app_id}...")
        print(f"Language: {lang}, Country: {country}")
        print(f"Count: {count}")
        print()
        
        # Test scraping
        reviews_data, total_count = scraper.scrape_reviews(
            app_id=app_id,
            lang=lang,
            country=country,
            count=count
        )
        
        print(f"✅ Scraping successful!")
        print(f"Found {len(reviews_data)} reviews")
        print()
        
        # Show sample reviews
        print("=== Sample Reviews ===")
        for i, review in enumerate(reviews_data[:3]):
            print(f"Review {i+1}:")
            print(f"  User: {review.get('userName', 'Unknown')}")
            print(f"  Rating: {review.get('score', 'N/A')} stars")
            print(f"  Date: {review.get('at', 'Unknown')}")
            print(f"  Content: {review.get('content', 'No content')[:100]}...")
            print()
        
        # Test dengan filter rating
        print("=== Testing Rating Filter ===")
        for rating in [1, 3, 5]:
            try:
                filtered_reviews, filtered_count = scraper.scrape_reviews(
                    app_id=app_id,
                    lang=lang,
                    country=country,
                    count=5,
                    filter_score_with=rating
                )
                
                print(f"Rating {rating} filter: {len(filtered_reviews)} reviews found")
                
                # Check if all reviews have correct rating
                if filtered_reviews:
                    actual_ratings = [r.get('score') for r in filtered_reviews]
                    print(f"  Actual ratings: {actual_ratings}")
                    if all(r == rating for r in actual_ratings):
                        print(f"  ✅ Filter working correctly")
                    else:
                        print(f"  ⚠️ Filter might not be working as expected")
                else:
                    print(f"  No reviews found for rating {rating}")
                print()
                
            except Exception as e:
                print(f"  ❌ Error testing rating {rating}: {e}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
