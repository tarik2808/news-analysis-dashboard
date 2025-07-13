import spacy
import pandas as pd
from collections import Counter
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re

class NLPAnalyzer:
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
            
        # Load spaCy model
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            print("Downloading spaCy model...")
            spacy.cli.download('en_core_web_sm')
            self.nlp = spacy.load('en_core_web_sm')
            
        self.stop_words = set(stopwords.words('english'))
        
    def extract_keywords(self, text, top_n=10):
        """Extract keywords from text using spaCy."""
        doc = self.nlp(text)
        
        # Extract nouns and proper nouns
        keywords = [token.text.lower() for token in doc 
                   if token.pos_ in ['NOUN', 'PROPN'] 
                   and token.text.lower() not in self.stop_words
                   and len(token.text) > 2]
        
        # Count keyword frequencies
        keyword_freq = Counter(keywords)
        
        return dict(keyword_freq.most_common(top_n))
        
    def extract_named_entities(self, text):
        """Extract named entities from text using spaCy."""
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
            
        return entities
        
    def analyze_sentiment(self, text):
        """Analyze sentiment of text using TextBlob."""
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
    analyzer = NLPAnalyzer()
    
    # Example text
    test_text = "Apple Inc. announced a new iPhone model in California. The company's stock price increased by 5%."
    
    # Analyze the text
    analysis = analyzer.analyze_article(test_text)
    
    print("Keywords:", analysis['keywords'])
    print("\nNamed Entities:", analysis['entities'])
    print("\nSentiment:", analysis['sentiment']) 