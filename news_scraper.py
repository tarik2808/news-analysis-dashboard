import requests
from bs4 import BeautifulSoup
from newspaper import Article
import pandas as pd
from datetime import datetime
import time
import random

class NewsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def scrape_bbc(self, num_articles=10):
        """Scrape articles from BBC News homepage."""
        articles = []
        try:
            response = requests.get('https://www.bbc.com/news', headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find article links using both new and legacy selectors
            links = soup.find_all('a', attrs={'data-testid': 'internal-link'})
            if not links:
                links = soup.find_all('a', {'class': 'gs-c-promo-heading'})
            else:
                # Also add legacy links if not already present
                legacy_links = soup.find_all('a', {'class': 'gs-c-promo-heading'})
                links += [l for l in legacy_links if l not in links]
            
            for link in links[:num_articles]:
                try:
                    article_url = 'https://www.bbc.com' + link['href'] if link['href'].startswith('/') else link['href']
                    article = Article(article_url)
                    article.download()
                    article.parse()
                    
                    articles.append({
                        'source': 'BBC',
                        'title': article.title,
                        'text': article.text,
                        'url': article_url,
                        'date': article.publish_date if article.publish_date else datetime.now(),
                        'keywords': article.keywords
                    })
                    
                    # Be nice to the server
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    print(f"Error scraping BBC article: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error accessing BBC News: {str(e)}")
            
        return articles
    
    def scrape_cnn(self, num_articles=10):
        """Scrape articles from CNN homepage."""
        articles = []
        try:
            response = requests.get('https://www.cnn.com', headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find article links
            links = soup.find_all('a', {'class': 'container__link'})
            
            for link in links[:num_articles]:
                try:
                    article_url = link['href']
                    if not article_url.startswith('http'):
                        article_url = 'https://www.cnn.com' + article_url
                        
                    article = Article(article_url)
                    article.download()
                    article.parse()
                    
                    articles.append({
                        'source': 'CNN',
                        'title': article.title,
                        'text': article.text,
                        'url': article_url,
                        'date': article.publish_date if article.publish_date else datetime.now(),
                        'keywords': article.keywords
                    })
                    
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    print(f"Error scraping CNN article: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error accessing CNN: {str(e)}")
            
        return articles
    
    def scrape_reuters(self, num_articles=10):
        """Scrape articles from Reuters homepage."""
        articles = []
        try:
            response = requests.get('https://www.reuters.com', headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find article links using both new and legacy selectors
            links = soup.find_all('a', attrs={'data-testid': 'Heading'})
            if not links:
                links = soup.find_all('a', {'class': 'story-title'})
            else:
                # Also add legacy links if not already present
                legacy_links = soup.find_all('a', {'class': 'story-title'})
                links += [l for l in legacy_links if l not in links]
            
            for link in links[:num_articles]:
                try:
                    article_url = link['href']
                    if not article_url.startswith('http'):
                        article_url = 'https://www.reuters.com' + article_url
                        
                    article = Article(article_url)
                    article.download()
                    article.parse()
                    
                    articles.append({
                        'source': 'Reuters',
                        'title': article.title,
                        'text': article.text,
                        'url': article_url,
                        'date': article.publish_date if article.publish_date else datetime.now(),
                        'keywords': article.keywords
                    })
                    
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    print(f"Error scraping Reuters article: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error accessing Reuters: {str(e)}")
            
        return articles
    
    def scrape_all_sources(self, articles_per_source=10):
        """Scrape articles from all sources."""
        all_articles = []
        
        # Scrape from each source
        all_articles.extend(self.scrape_bbc(articles_per_source))
        all_articles.extend(self.scrape_cnn(articles_per_source))
        all_articles.extend(self.scrape_reuters(articles_per_source))
        
        # Convert to DataFrame
        df = pd.DataFrame(all_articles)
        
        # Save to CSV
        df.to_csv('scraped_articles.csv', index=False)
        
        return df

if __name__ == "__main__":
    # Test the scraper
    scraper = NewsScraper()
    articles_df = scraper.scrape_all_sources(articles_per_source=5)
    print(f"Scraped {len(articles_df)} articles in total") 