#!/usr/bin/env python3
"""
Debug script for trend analysis
"""

import pandas as pd
from trend_analyzer import TrendAnalyzer

def test_trend_analysis():
    """Test trend analysis with sample data"""
    print("🧪 Testing Trend Analysis...")
    
    # Create sample data similar to what the API receives
    sample_data = {
        'source': ['BBC', 'CNN', 'Reuters', 'BBC', 'CNN', 'Reuters'],
        'title': ['Article 1', 'Article 2', 'Article 3', 'Article 4', 'Article 5', 'Article 6'],
        'text': ['Content 1', 'Content 2', 'Content 3', 'Content 4', 'Content 5', 'Content 6'],
        'url': ['url1', 'url2', 'url3', 'url4', 'url5', 'url6'],
        'date': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01'],
        'keywords': [{}, {}, {}, {}, {}, {}],  # Empty keywords
        'sentiment_polarity': [0.1, -0.2, 0.3, -0.1, 0.2, -0.3]
    }
    
    df = pd.DataFrame(sample_data)
    print(f"✅ Created DataFrame with {len(df)} rows")
    
    try:
        trend_analyzer = TrendAnalyzer()
        
        # Test each method individually
        print("📊 Testing extract_trending_keywords...")
        keywords = trend_analyzer.extract_trending_keywords(df)
        print(f"✅ Keywords extracted: {keywords}")
        
        print("📈 Testing analyze_source_trends...")
        source_trends = trend_analyzer.analyze_source_trends(df)
        print(f"✅ Source trends: {source_trends}")
        
        print("⏰ Testing analyze_temporal_trends...")
        temporal_trends = trend_analyzer.analyze_temporal_trends(df)
        print(f"✅ Temporal trends: {temporal_trends}")
        
        print("🎉 All trend analysis tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in trend analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_trend_analysis() 