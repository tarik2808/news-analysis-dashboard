import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
import string
import pandas as pd

class TextProcessor:
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
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
            
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
    def clean_text(self, text):
        """Clean and preprocess text."""
        if not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
        
    def remove_stopwords(self, text):
        """Remove stopwords from text."""
        word_tokens = word_tokenize(text)
        filtered_text = [word for word in word_tokens if word not in self.stop_words]
        return ' '.join(filtered_text)
        
    def lemmatize_text(self, text):
        """Lemmatize text."""
        word_tokens = word_tokenize(text)
        lemmatized_text = [self.lemmatizer.lemmatize(word) for word in word_tokens]
        return ' '.join(lemmatized_text)
        
    def process_article(self, text):
        """Process a single article's text."""
        cleaned_text = self.clean_text(text)
        text_without_stopwords = self.remove_stopwords(cleaned_text)
        processed_text = self.lemmatize_text(text_without_stopwords)
        return processed_text
        
    def process_dataframe(self, df):
        """Process all articles in a DataFrame."""
        # Create a copy to avoid modifying the original
        processed_df = df.copy()
        
        # Process the text column
        processed_df['processed_text'] = processed_df['text'].apply(self.process_article)
        
        # Save processed data
        processed_df.to_csv('processed_articles.csv', index=False)
        
        return processed_df

if __name__ == "__main__":
    # Test the processor
    processor = TextProcessor()
    
    # Example text
    test_text = "The quick brown foxes are jumping over the lazy dogs. Visit https://example.com for more info!"
    
    # Process the text
    processed_text = processor.process_article(test_text)
    print("Original text:", test_text)
    print("Processed text:", processed_text) 