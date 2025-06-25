#!/usr/bin/env python3
"""
Simple test runner for the News Analysis Project
"""

import subprocess
import sys
import os
import time

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*50}")
    print(f"Testing: {description}")
    print(f"Command: {command}")
    print(f"{'='*50}")
    
    try:
        start_time = time.time()
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        end_time = time.time()
        
        if result.returncode == 0:
            print(f"✓ PASSED in {end_time - start_time:.2f} seconds")
            if result.stdout.strip():
                print("Output:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            return True
        else:
            print(f"✗ FAILED (return code: {result.returncode})")
            if result.stderr.strip():
                print("Error:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ FAILED - Timeout (5 minutes)")
        return False
    except Exception as e:
        print(f"✗ FAILED - Exception: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    try:
        import requests
        import beautifulsoup4
        import newspaper3k
        import nltk
        import spacy
        import pandas
        import matplotlib
        import seaborn
        import wordcloud
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_nltk_data():
    """Check if NLTK data is available"""
    print("Checking NLTK data...")
    
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
        print("✓ NLTK data is available")
        return True
    except LookupError as e:
        print(f"✗ Missing NLTK data: {e}")
        print("Please run the NLTK download commands")
        return False

def check_spacy_model():
    """Check if spaCy model is available"""
    print("Checking spaCy model...")
    
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("✓ spaCy model is available")
        return True
    except OSError:
        print("✗ spaCy model not found")
        print("Please run: python -m spacy download en_core_web_sm")
        return False

def main():
    """Main test runner"""
    print("News Analysis Project - Test Runner")
    print("="*50)
    
    # Check prerequisites
    if not check_dependencies():
        return False
    
    if not check_nltk_data():
        return False
    
    if not check_spacy_model():
        return False
    
    # Test individual components
    tests = [
        ("python text_processor.py", "Text Processor"),
        ("python nlp_analyzer.py", "NLP Analyzer"),
        ("python trend_analyzer.py", "Trend Analyzer"),
        ("python news_scraper.py", "News Scraper (small test)"),
    ]
    
    passed = 0
    total = len(tests)
    
    for command, description in tests:
        if run_command(command, description):
            passed += 1
    
    # Test full pipeline (optional - takes longer)
    print(f"\n{'='*50}")
    print("Full Pipeline Test (Optional)")
    print("This will scrape real articles and may take several minutes.")
    print("Press Enter to skip, or type 'run' to continue...")
    
    user_input = input().strip().lower()
    if user_input == 'run':
        if run_command("python main.py", "Full Pipeline"):
            passed += 1
        total += 1
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 