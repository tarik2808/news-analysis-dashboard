import pandas as pd
from collections import Counter
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import re

class SimpleNLPAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger')
            
        self.stop_words = set(stopwords.words('english'))
        
    def extract_keywords(self, text, top_n=10):
        """Extract keywords from text using NLTK POS tagging."""
        if not isinstance(text, str) or not text.strip():
            return {}
            
        # Tokenize and tag parts of speech
        tokens = word_tokenize(text.lower())
        pos_tags = pos_tag(tokens)
        
        # Extract nouns and proper nouns
        keywords = []
        for word, tag in pos_tags:
            if (tag.startswith('NN') and  # Nouns
                word not in self.stop_words and
                len(word) > 2 and
                word.isalpha()):
                keywords.append(word)
        
        # Count keyword frequencies
        keyword_freq = Counter(keywords)
        
        return dict(keyword_freq.most_common(top_n))
        
    def extract_named_entities(self, text):
        """Extract named entities using simple pattern matching."""
        if not isinstance(text, str) or not text.strip():
            return {}
            
        entities = {
            'PERSON': [],
            'ORGANIZATION': [],
            'LOCATION': [],
            'MISC': []
        }
        
        # Simple pattern matching for entities
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        
        for word, tag in pos_tags:
            if tag == 'NNP':  # Proper noun
                if len(word) > 1:
                    # Simple heuristics for entity types
                    if word.lower() in ['apple', 'microsoft', 'google', 'amazon', 'tesla', 'facebook']:
                        entities['ORGANIZATION'].append(word)
                    elif word.lower() in ['california', 'new york', 'london', 'tokyo', 'paris']:
                        entities['LOCATION'].append(word)
                    else:
                        entities['PERSON'].append(word)
        
        # Remove empty categories
        return {k: v for k, v in entities.items() if v}
        
    def analyze_sentiment(self, text):
        """Analyze sentiment of text using TextBlob."""
        if not isinstance(text, str) or not text.strip():
            return {'polarity': 0.0, 'subjectivity': 0.0}
            
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,  # -1 to 1
            'subjectivity': blob.sentiment.subjectivity  # 0 to 1
        }
        
    def analyze_article(self, text):
        """Perform all NLP analyses on a single article."""
        return {
            'keywords': self.extract_keywords(text),
            'entities': self.extract_named_entities(text),
            'sentiment': self.analyze_sentiment(text)
        }
        
    def analyze_dataframe(self, df):
        """Analyze all articles in a DataFrame."""
        # Create a copy to avoid modifying the original
        analyzed_df = df.copy()
        
        # Add analysis columns
        analyzed_df['keywords'] = analyzed_df['processed_text'].apply(self.extract_keywords)
        analyzed_df['entities'] = analyzed_df['processed_text'].apply(self.extract_named_entities)
        analyzed_df['sentiment'] = analyzed_df['processed_text'].apply(self.analyze_sentiment)
        
        # Extract sentiment scores
        analyzed_df['sentiment_polarity'] = analyzed_df['sentiment'].apply(lambda x: x['polarity'])
        analyzed_df['sentiment_subjectivity'] = analyzed_df['sentiment'].apply(lambda x: x['subjectivity'])
        
        # Save analyzed data
        analyzed_df.to_csv('analyzed_articles.csv', index=False)
        
        return analyzed_df

if __name__ == "__main__":
    # Test the analyzer
    analyzer = SimpleNLPAnalyzer()
    
    # Example text
    test_text = "Apple Inc. announced a new iPhone model in California. The company's stock price increased by 5%."
    
    # Analyze the text
    analysis = analyzer.analyze_article(test_text)
    
    print("Keywords:", analysis['keywords'])
    print("\nNamed Entities:", analysis['entities'])
    print("\nSentiment:", analysis['sentiment']) 