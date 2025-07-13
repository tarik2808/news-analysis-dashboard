import os
from news_scraper import NewsScraper
from text_processor import TextProcessor
from nlp_analyzer import NLPAnalyzer
from trend_analyzer import TrendAnalyzer
import pandas as pd
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_analysis.log'),
        logging.StreamHandler()
    ]
)

def create_output_directories():
    """Create necessary output directories."""
    directories = ['data', 'trend_plots', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main function to run the news analysis pipeline."""
    try:
        # Create output directories
        create_output_directories()
        logging.info("Created output directories")
        
        # Initialize components
        scraper = NewsScraper()
        processor = TextProcessor()
        analyzer = NLPAnalyzer()
        trend_analyzer = TrendAnalyzer()
        
        # Step 1: Scrape news articles
        logging.info("Starting news scraping...")
        articles_df = scraper.scrape_all_sources(articles_per_source=10)
        logging.info(f"Scraped {len(articles_df)} articles")
        
        # Step 2: Process text
        logging.info("Processing article text...")
        processed_df = processor.process_dataframe(articles_df)
        logging.info("Text processing completed")
        
        # Step 3: Perform NLP analysis
        logging.info("Performing NLP analysis...")
        analyzed_df = analyzer.analyze_dataframe(processed_df)
        logging.info("NLP analysis completed")
        
        # Step 4: Analyze trends
        logging.info("Analyzing trends...")
        trends = trend_analyzer.analyze_trends(analyzed_df)
        logging.info("Trend analysis completed")
        
        # Print summary
        print("\nAnalysis Summary:")
        print(f"Total articles analyzed: {len(analyzed_df)}")
        print("\nTop 5 trending keywords:")
        for keyword, count in list(trends['keywords'].items())[:5]:
            print(f"- {keyword}: {count} occurrences")
            
        print("\nArticle distribution by source:")
        for source, count in trends['source']['article_counts'].items():
            print(f"- {source}: {count} articles")
            
        print("\nAnalysis results have been saved to:")
        print("- scraped_articles.csv")
        print("- processed_articles.csv")
        print("- analyzed_articles.csv")
        print("- trend_plots/ directory")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 