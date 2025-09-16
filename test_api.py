#!/usr/bin/env python3
"""
Test script untuk mengecek API Flask endpoint
"""

import requests
import json
import time

def test_flask_api():
    """Test Flask API endpoints"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== Testing Flask API Endpoints ===")
    
    # Test 1: Homepage
    print("1. Testing homepage...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✅ Homepage accessible")
        else:
            print(f"   ❌ Homepage error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Homepage error: {e}")
    
    # Test 2: Scrape endpoint
    print("\n2. Testing scrape_reviews endpoint...")
    try:
        payload = {
            "app_id": "com.whatsapp",
            "count": 5,
            "lang": "id", 
            "country": "id"
        }
        
        print(f"   Sending request: {payload}")
        response = requests.post(
            f"{base_url}/scrape_reviews",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Scrape endpoint successful!")
            print(f"   Response: {data}")
        else:
            print(f"   ❌ Scrape endpoint error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Scrape endpoint error: {e}")
    
    # Test 3: Scrape with rating filter
    print("\n3. Testing scrape with rating filter...")
    try:
        payload = {
            "app_id": "com.whatsapp",
            "count": 3,
            "lang": "id", 
            "country": "id",
            "filter_score": 5
        }
        
        print(f"   Sending request with rating filter: {payload}")
        response = requests.post(
            f"{base_url}/scrape_reviews",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Rating filter endpoint successful!")
            print(f"   Response: {data}")
        else:
            print(f"   ❌ Rating filter endpoint error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Rating filter endpoint error: {e}")

if __name__ == "__main__":
    # Check if server is running first
    print("Checking if Flask server is running...")
    try:
        response = requests.get("http://127.0.0.1:5000/", timeout=5)
        print("✅ Server is running!")
        test_flask_api()
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("\nPlease make sure Flask server is running:")
        print("python app.py")
