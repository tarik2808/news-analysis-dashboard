import requests

# 1. Scrape latest articles
print('Scraping latest articles...')
scrape_result = requests.post('http://localhost:8000/scrape', json={'articles_per_source': 10})
articles = scrape_result.json()['articles']
print(f'Scraped {len(articles)} articles')

# 2. Analyze sentiment and keywords
print('Analyzing sentiment and keywords...')
texts = [a['text'] for a in articles]
analyze_result = requests.post('http://localhost:8000/analyze', json={'texts': texts, 'pipeline': 'simple'})
analysis = analyze_result.json()['results']
for article, result in zip(articles, analysis):
    article['sentiment_polarity'] = result.get('sentiment_polarity', 0.0)
    article['keywords'] = result.get('keywords', {})

# 3. Prepare data for trends endpoint
print('Preparing trends data...')
trends_data = {
    'source': [a['source'] for a in articles],
    'title': [a['title'] for a in articles],
    'text': [a['text'] for a in articles],
    'url': [a['url'] for a in articles],
    'date': [a['date'] for a in articles],
    'keywords': [a.get('keywords', {}) for a in articles],
    'sentiment_polarity': [a.get('sentiment_polarity', 0.0) for a in articles]
}

# 4. Run trends analysis
print('Running trends analysis...')
trends_result = requests.post('http://localhost:8000/trends', json=trends_data)
print(f'Trends status: {trends_result.status_code}')
print('Trends response:', trends_result.text[:500]) 