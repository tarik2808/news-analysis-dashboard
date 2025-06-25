#!/usr/bin/env python3
"""
Test script for the News Analysis Platform
Tests both frontend and backend functionality
"""

import requests
import time
import subprocess
import sys
from pathlib import Path

def test_backend_api():
    """Test the backend API endpoints"""
    print("🧪 Testing Backend API...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
            
        # Test scrape endpoint
        print("📰 Testing news scraping...")
        scrape_response = requests.post(
            f"{base_url}/scrape",
            json={"articles_per_source": 3},
            timeout=30
        )
        
        if scrape_response.status_code == 200:
            data = scrape_response.json()
            print(f"✅ Scraped {len(data.get('articles', []))} articles")
            
            # Test trends endpoint with scraped data
            if data.get('articles'):
                print("📊 Testing trend analysis...")
                articles = data['articles']
                
                trend_data = {
                    "source": [article.get('source', 'Unknown') for article in articles],
                    "title": [article.get('title', '') for article in articles],
                    "text": [article.get('text', '') for article in articles],
                    "url": [article.get('url', '') for article in articles],
                    "date": [article.get('date', '2024-01-01') for article in articles]
                }
                
                trends_response = requests.post(
                    f"{base_url}/trends",
                    json=trend_data,
                    timeout=30
                )
                
                if trends_response.status_code == 200:
                    trends_data = trends_response.json()
                    print(f"✅ Trend analysis completed - {len(trends_data.get('top_keywords', {}))} keywords found")
                else:
                    print(f"❌ Trend analysis failed: {trends_response.status_code}")
                    
        else:
            print(f"❌ Scraping failed: {scrape_response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running. Start it with: uvicorn api:app --host 0.0.0.0 --port 8000 --reload")
        return False
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def test_frontend():
    """Test if frontend is accessible"""
    print("🎨 Testing Frontend...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not running. Start it with: cd frontend && npm start")
        return False
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 News Analysis Platform - System Test")
    print("=" * 50)
    
    # Test backend
    backend_ok = test_backend_api()
    
    print()
    
    # Test frontend
    frontend_ok = test_frontend()
    
    print()
    print("=" * 50)
    
    if backend_ok and frontend_ok:
        print("🎉 All tests passed! Your application is working correctly.")
        print("\n🌐 Access your application at:")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        
        if not backend_ok:
            print("\n🔧 To start the backend:")
            print("   uvicorn api:app --host 0.0.0.0 --port 8000 --reload")
            
        if not frontend_ok:
            print("\n🔧 To start the frontend:")
            print("   cd frontend")
            print("   npm start")
            
        print("\n💡 Or use the combined startup script:")
        print("   python start_app.py")

if __name__ == "__main__":
    main() 