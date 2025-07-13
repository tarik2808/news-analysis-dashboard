# Testing Guide for News Analysis Project

## Overview
This project is a news scraping and analysis pipeline that processes articles from multiple sources and performs NLP analysis. Here are different ways to test the project:

## 1. Quick Start Testing

### Prerequisites
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download required NLTK data (will be done automatically, but you can pre-download):
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

3. Download spaCy model:
```bash
python -m spacy download en_core_web_sm
```

### Basic Functionality Test
Run the main pipeline with a small number of articles:
```bash
python main.py
```

This will:
- Scrape 10 articles from each source (30 total)
- Process the text
- Perform NLP analysis
- Generate trend visualizations
- Save results to CSV files

## 2. Individual Component Testing

### Test News Scraper
```bash
python news_scraper.py
```
This will test scraping 5 articles from each source.

### Test Text Processor
```bash
python text_processor.py
```
This will test text cleaning, stopword removal, and lemmatization.

### Test NLP Analyzer
```bash
python nlp_analyzer.py
```
This will test keyword extraction, named entity recognition, and sentiment analysis.

### Test Trend Analyzer
```bash
python trend_analyzer.py
```
This will test trend analysis and visualization generation.

## 3. Unit Testing

Create a `tests` directory and add unit tests:

### Example Unit Test Structure
```
tests/
├── test_news_scraper.py
├── test_text_processor.py
├── test_nlp_analyzer.py
├── test_trend_analyzer.py
└── test_integration.py
```

### Sample Unit Test (test_text_processor.py)
```python
import unittest
from text_processor import TextProcessor

class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TextProcessor()
    
    def test_clean_text(self):
        test_text = "Hello World! Visit https://example.com for more info."
        cleaned = self.processor.clean_text(test_text)
        self.assertNotIn("https://example.com", cleaned)
        self.assertNotIn("!", cleaned)
    
    def test_remove_stopwords(self):
        test_text = "the quick brown fox jumps over the lazy dog"
        result = self.processor.remove_stopwords(test_text)
        self.assertNotIn("the", result)
        self.assertIn("quick", result)

if __name__ == '__main__':
    unittest.main()
```

## 4. Integration Testing

### Test Complete Pipeline
Create a test that runs the entire pipeline with mock data:

```python
# test_integration.py
import pandas as pd
from news_scraper import NewsScraper
from text_processor import TextProcessor
from nlp_analyzer import NLPAnalyzer
from trend_analyzer import TrendAnalyzer

def test_pipeline():
    # Create mock data
    mock_data = {
        'source': ['BBC', 'CNN', 'Reuters'],
        'title': ['Test Article 1', 'Test Article 2', 'Test Article 3'],
        'text': [
            'Apple Inc. announced a new iPhone model in California.',
            'Microsoft released Windows 11 with new features.',
            'Google launched a new AI service for developers.'
        ],
        'url': ['http://test1.com', 'http://test2.com', 'http://test3.com'],
        'date': [pd.Timestamp.now()] * 3,
        'keywords': [[], [], []]
    }
    
    df = pd.DataFrame(mock_data)
    
    # Test each component
    processor = TextProcessor()
    processed_df = processor.process_dataframe(df)
    
    analyzer = NLPAnalyzer()
    analyzed_df = analyzer.analyze_dataframe(processed_df)
    
    trend_analyzer = TrendAnalyzer()
    trends = trend_analyzer.analyze_trends(analyzed_df)
    
    # Assertions
    assert len(processed_df) == 3
    assert 'processed_text' in processed_df.columns
    assert 'sentiment_polarity' in analyzed_df.columns
    assert 'keywords' in trends
    
    print("Integration test passed!")

if __name__ == "__main__":
    test_pipeline()
```

## 5. Performance Testing

### Test with Different Article Counts
```python
# performance_test.py
import time
from news_scraper import NewsScraper

def test_scraping_performance():
    scraper = NewsScraper()
    
    for count in [5, 10, 20]:
        start_time = time.time()
        articles_df = scraper.scrape_all_sources(articles_per_source=count)
        end_time = time.time()
        
        print(f"Scraped {len(articles_df)} articles in {end_time - start_time:.2f} seconds")
        print(f"Average time per article: {(end_time - start_time) / len(articles_df):.2f} seconds")

if __name__ == "__main__":
    test_scraping_performance()
```

## 6. Error Handling Testing

### Test Network Failures
```python
# error_test.py
import requests
from unittest.mock import patch
from news_scraper import NewsScraper

def test_network_errors():
    scraper = NewsScraper()
    
    # Test with mock network failure
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")
        
        articles = scraper.scrape_bbc(num_articles=5)
        assert len(articles) == 0  # Should handle error gracefully

if __name__ == "__main__":
    test_network_errors()
```

## 7. Data Quality Testing

### Test Output Files
```python
# data_quality_test.py
import pandas as pd
import os

def test_output_files():
    # Run the main pipeline first
    os.system("python main.py")
    
    # Check if output files exist
    files_to_check = [
        'scraped_articles.csv',
        'processed_articles.csv', 
        'analyzed_articles.csv'
    ]
    
    for file in files_to_check:
        assert os.path.exists(file), f"Output file {file} not found"
        
        # Load and check data quality
        df = pd.read_csv(file)
        assert len(df) > 0, f"File {file} is empty"
        
        # Check for required columns
        if 'scraped_articles.csv' in file:
            required_cols = ['source', 'title', 'text', 'url', 'date']
        elif 'processed_articles.csv' in file:
            required_cols = ['source', 'title', 'text', 'processed_text']
        elif 'analyzed_articles.csv' in file:
            required_cols = ['source', 'title', 'text', 'processed_text', 'sentiment_polarity']
            
        for col in required_cols:
            assert col in df.columns, f"Required column {col} missing from {file}"
    
    print("Data quality test passed!")

if __name__ == "__main__":
    test_output_files()
```

## 8. Visual Testing

### Check Generated Plots
After running the pipeline, verify that these files are generated in the `trend_plots/` directory:
- `temporal_trends.png`
- `source_distribution.png`
- `sentiment_by_source.png`
- `wordcloud.png`

## 9. Automated Testing Script

Create a comprehensive test runner:

```python
# run_tests.py
import subprocess
import sys
import os

def run_tests():
    tests = [
        "python news_scraper.py",
        "python text_processor.py", 
        "python nlp_analyzer.py",
        "python trend_analyzer.py",
        "python main.py"
    ]
    
    for test in tests:
        print(f"Running: {test}")
        try:
            result = subprocess.run(test, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {test} passed")
            else:
                print(f"✗ {test} failed")
                print(f"Error: {result.stderr}")
        except Exception as e:
            print(f"✗ {test} failed with exception: {e}")

if __name__ == "__main__":
    run_tests()
```

## 10. Testing Checklist

- [ ] Dependencies installed correctly
- [ ] NLTK data downloaded
- [ ] spaCy model downloaded
- [ ] Individual components work
- [ ] Integration pipeline works
- [ ] Output files generated
- [ ] Visualizations created
- [ ] Error handling works
- [ ] Performance is acceptable
- [ ] Data quality is good

## 11. Common Issues and Solutions

### Issue: NLTK data not found
**Solution**: Run `nltk.download()` commands manually

### Issue: spaCy model not found
**Solution**: Run `python -m spacy download en_core_web_sm`

### Issue: Network timeouts during scraping
**Solution**: Increase timeout values or add retry logic

### Issue: Memory issues with large datasets
**Solution**: Process data in batches or reduce article count

### Issue: Missing output directories
**Solution**: The main script creates them automatically, but you can create manually:
```python
import os
os.makedirs('data', exist_ok=True)
os.makedirs('trend_plots', exist_ok=True)
os.makedirs('logs', exist_ok=True)
```

## 12. Continuous Testing

For ongoing development, consider setting up:
- Automated test runs on code changes
- Performance benchmarks
- Data quality monitoring
- Error logging and alerting

This comprehensive testing approach will help ensure your news analysis project works reliably and produces quality results. 
