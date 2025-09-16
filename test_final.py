#!/usr/bin/env python3
"""
Final test script untuk semua fitur SentiPlay
"""

import requests
import json
import time

def test_all_features():
    """Test semua fitur aplikasi"""
    base_url = "http://127.0.0.1:5000"
    
    print("🚀 SentiPlay Feature Test")
    print("=" * 40)
    
    # Test 1: Test sort NEWEST
    print("\n1. Testing NEWEST sort...")
    test_scraping(base_url, "NEWEST")
    
    # Test 2: Test sort MOST_RELEVANT 
    print("\n2. Testing MOST_RELEVANT sort...")
    test_scraping(base_url, "MOST_RELEVANT")
    
    # Test 3: Test dengan rating filter
    print("\n3. Testing with rating filter...")
    test_with_rating_filter(base_url)
    
    print("\n✅ All tests completed!")

def test_scraping(base_url, sort_type):
    """Test scraping dengan sort parameter"""
    payload = {
        "app_id": "com.whatsapp",
        "count": 5,
        "lang": "id", 
        "country": "id",
        "sort": sort_type
    }
    
    try:
        print(f"   Sending request with sort={sort_type}...")
        response = requests.post(
            f"{base_url}/api/scrape",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"   ✅ Scraping started! Session ID: {session_id}")
            
            # Wait and check status
            time.sleep(3)
            status_response = requests.get(f"{base_url}/api/scrape/status/{session_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   📊 Status: {status_data.get('status')}, Reviews: {status_data.get('review_count')}")
            
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_with_rating_filter(base_url):
    """Test scraping dengan rating filter"""
    payload = {
        "app_id": "com.whatsapp",
        "count": 3,
        "lang": "id", 
        "country": "id",
        "sort": "NEWEST",
        "filter_score": 5
    }
    
    try:
        print("   Testing with 5-star rating filter...")
        response = requests.post(
            f"{base_url}/api/scrape",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"   ✅ Rating filter scraping started! Session ID: {session_id}")
            
            # Wait and check status
            time.sleep(3)
            status_response = requests.get(f"{base_url}/api/scrape/status/{session_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   📊 Status: {status_data.get('status')}, Reviews: {status_data.get('review_count')}")
            
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:5000/", timeout=5)
        if response.status_code == 200:
            test_all_features()
        else:
            print("❌ Server not responding correctly")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("\nMake sure Flask server is running:")
        print("python app.py")
