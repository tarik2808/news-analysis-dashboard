import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns

class TrendAnalyzer:
    def __init__(self):
        self.trends = {}
        
    def extract_trending_keywords(self, df, top_n=20):
        """Extract trending keywords across all articles."""
        all_keywords = []
        
        # Combine all keywords from articles
        for keywords_dict in df['keywords']:
            # Handle different types of keywords data
            if keywords_dict is None:
                continue
            elif isinstance(keywords_dict, dict):
                for k, v in keywords_dict.items():
                    if isinstance(k, str) and k.strip() and k != "0":
                        all_keywords.extend([k] * v)
            elif isinstance(keywords_dict, str):
                # If it's a string, split by spaces or commas
                keywords = keywords_dict.split()
                all_keywords.extend(keywords)
            elif isinstance(keywords_dict, list):
                # If it's a list, add all items
                all_keywords.extend(keywords_dict)
            else:
                # Skip if it's not a recognized format
                continue
            
        # Count keyword frequencies
        keyword_freq = Counter(all_keywords)
        # Log the top 10 keywords for debugging
        print("[DEBUG] Top 10 keywords:", keyword_freq.most_common(10))
        return dict(keyword_freq.most_common(top_n))
        
    def analyze_temporal_trends(self, df, time_window='D'):
        """Analyze trends over time."""
        print("[DEBUG] Raw date values:", list(df['date']))
        try:
            # Let pandas auto-detect the format - it handles ISO8601 well
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        except Exception as e:
            print("[ERROR] pandas.to_datetime failed:", e)
            # Try parsing each value individually to find the culprit
            for i, val in enumerate(df['date']):
                try:
                    pd.to_datetime(val, errors='raise')
                except Exception as indiv_e:
                    print(f"[ERROR] Failed to parse date at index {i}: {val} -> {indiv_e}")
            # Last resort: fill with current time
            df['date'] = pd.Timestamp.now()
        
        print("[DEBUG] Parsed date values:", list(df['date']))
        # Remove any NaT values and fill with current time
        df['date'] = df['date'].fillna(pd.Timestamp.now())
        
        # Ensure all dates are timezone-naive
        def make_tz_naive(dt):
            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt
        df['date'] = df['date'].apply(make_tz_naive)
        
        # Group by time window and count articles
        temporal_trends = df.groupby(pd.Grouper(key='date', freq=time_window)).size()
        
        return temporal_trends
        
    def analyze_source_trends(self, df):
        """Analyze trends by news source."""
        # Count articles by source
        source_counts = df['source'].value_counts()
        
        # Calculate average sentiment by source
        source_sentiment = df.groupby('source')['sentiment_polarity'].mean()
        
        return {
            'article_counts': source_counts,
            'sentiment_by_source': source_sentiment
        }
        
    def generate_wordcloud(self, df, output_file='wordcloud.png'):
        """Generate a word cloud from article keywords."""
        # Combine all keywords with proper handling
        all_keywords = []
        for keywords_dict in df['keywords']:
            if keywords_dict is None:
                continue
            elif isinstance(keywords_dict, dict):
                for k, v in keywords_dict.items():
                    all_keywords.extend([k] * v)
            elif isinstance(keywords_dict, str):
                keywords = keywords_dict.split()
                all_keywords.extend(keywords)
            elif isinstance(keywords_dict, list):
                all_keywords.extend(keywords_dict)
            else:
                continue
        
        # Join keywords into a single string
        keywords_text = ' '.join(all_keywords)
        
        # Generate word cloud only if we have keywords
        if keywords_text.strip():
            wordcloud = WordCloud(width=800, height=400, 
                                background_color='white',
                                max_words=100).generate(keywords_text)
            
            # Plot and save
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.savefig(output_file)
            plt.close()
        else:
            # Create a simple placeholder if no keywords
            plt.figure(figsize=(10, 5))
            plt.text(0.5, 0.5, 'No keywords available', 
                    ha='center', va='center', fontsize=20)
            plt.axis('off')
            plt.savefig(output_file)
            plt.close()
        
    def plot_trends(self, df, output_dir='trend_plots'):
        """Generate various trend visualizations."""
        # Create output directory if it doesn't exist
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Temporal trends
        temporal_trends = self.analyze_temporal_trends(df)
        plt.figure(figsize=(12, 6))
        temporal_trends.plot()
        plt.title('Article Frequency Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Articles')
        plt.savefig(f'{output_dir}/temporal_trends.png')
        plt.close()
        
        # 2. Source distribution
        source_trends = self.analyze_source_trends(df)
        plt.figure(figsize=(10, 6))
        source_trends['article_counts'].plot(kind='bar')
        plt.title('Article Distribution by Source')
        plt.xlabel('News Source')
        plt.ylabel('Number of Articles')
        plt.savefig(f'{output_dir}/source_distribution.png')
        plt.close()
        
        # 3. Sentiment by source
        plt.figure(figsize=(10, 6))
        source_trends['sentiment_by_source'].plot(kind='bar')
        plt.title('Average Sentiment by Source')
        plt.xlabel('News Source')
        plt.ylabel('Average Sentiment Polarity')
        plt.savefig(f'{output_dir}/sentiment_by_source.png')
        plt.close()
        
        # 4. Generate word cloud
        self.generate_wordcloud(df, f'{output_dir}/wordcloud.png')
        
    def analyze_trends(self, df):
        """Perform all trend analyses."""
        # Extract trending keywords
        self.trends['keywords'] = self.extract_trending_keywords(df)
        
        # Analyze temporal trends
        self.trends['temporal'] = self.analyze_temporal_trends(df)
        
        # Analyze source trends
        self.trends['source'] = self.analyze_source_trends(df)
        
        # Generate visualizations
        self.plot_trends(df)
        
        return self.trends

if __name__ == "__main__":
    # Test the analyzer
    analyzer = TrendAnalyzer()
    
    # Create sample data
    data = {
        'date': pd.date_range(start='2024-01-01', periods=10),
        'source': ['BBC', 'CNN', 'Reuters'] * 3 + ['BBC'],
        'keywords': [{'apple': 5, 'iphone': 3}, {'microsoft': 4, 'windows': 2}] * 5,
        'sentiment_polarity': np.random.uniform(-1, 1, 10)
    }
    
    df = pd.DataFrame(data)
    
    # Analyze trends
    trends = analyzer.analyze_trends(df)
    
    print("Trending Keywords:", trends['keywords'])
    print("\nTemporal Trends:", trends['temporal'])
    print("\nSource Trends:", trends['source']) 