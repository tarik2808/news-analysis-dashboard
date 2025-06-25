#!/usr/bin/env python3
"""
Unit tests for the TextProcessor class
"""

import unittest
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_processor import TextProcessor

class TestTextProcessor(unittest.TestCase):
    """Test cases for TextProcessor class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.processor = TextProcessor()
        
    def test_clean_text_basic(self):
        """Test basic text cleaning functionality"""
        test_text = "Hello World! Visit https://example.com for more info."
        cleaned = self.processor.clean_text(test_text)
        
        # Should remove URLs
        self.assertNotIn("https://example.com", cleaned)
        # Should remove punctuation
        self.assertNotIn("!", cleaned)
        # Should convert to lowercase
        self.assertEqual(cleaned, cleaned.lower())
        
    def test_clean_text_with_numbers(self):
        """Test text cleaning with numbers"""
        test_text = "The year is 2024 and we have 5 new features."
        cleaned = self.processor.clean_text(test_text)
        
        # Should remove numbers
        self.assertNotIn("2024", cleaned)
        self.assertNotIn("5", cleaned)
        
    def test_clean_text_empty_input(self):
        """Test text cleaning with empty or None input"""
        # Test with None
        result = self.processor.clean_text(None)
        self.assertEqual(result, "")
        
        # Test with empty string
        result = self.processor.clean_text("")
        self.assertEqual(result, "")
        
        # Test with whitespace only
        result = self.processor.clean_text("   \n\t   ")
        self.assertEqual(result, "")
        
    def test_remove_stopwords(self):
        """Test stopword removal"""
        test_text = "the quick brown fox jumps over the lazy dog"
        result = self.processor.remove_stopwords(test_text)
        
        # Should remove common stopwords
        self.assertNotIn("the", result)
        self.assertNotIn("over", result)
        # Should keep content words
        self.assertIn("quick", result)
        self.assertIn("brown", result)
        self.assertIn("fox", result)
        
    def test_lemmatize_text(self):
        """Test text lemmatization"""
        test_text = "running jumping foxes dogs"
        result = self.processor.lemmatize_text(test_text)
        
        # Should lemmatize words
        self.assertIn("run", result)
        self.assertIn("jump", result)
        self.assertIn("fox", result)
        self.assertIn("dog", result)
        
    def test_process_article_complete(self):
        """Test complete article processing pipeline"""
        test_text = "The quick brown foxes are jumping over the lazy dogs! Visit https://example.com for more info."
        result = self.processor.process_article(test_text)
        
        # Should be cleaned and processed
        self.assertNotIn("https://example.com", result)
        self.assertNotIn("!", result)
        self.assertNotIn("the", result)  # stopword removed
        self.assertIn("quick", result)
        self.assertIn("brown", result)
        
    def test_process_dataframe(self):
        """Test processing a DataFrame of articles"""
        import pandas as pd
        
        # Create test DataFrame
        test_data = {
            'source': ['BBC', 'CNN'],
            'title': ['Test 1', 'Test 2'],
            'text': [
                'The quick brown fox jumps over the lazy dog.',
                'A new technology breakthrough in AI research.'
            ]
        }
        df = pd.DataFrame(test_data)
        
        # Process the DataFrame
        result_df = self.processor.process_dataframe(df)
        
        # Check that processed_text column was added
        self.assertIn('processed_text', result_df.columns)
        self.assertEqual(len(result_df), 2)
        
        # Check that text was processed
        self.assertNotIn('the', result_df.iloc[0]['processed_text'])
        self.assertIn('quick', result_df.iloc[0]['processed_text'])

    def test_only_punctuation(self):
        """Test text cleaning with only punctuation"""
        test_text = "!!!...,,,;;;"
        cleaned = self.processor.clean_text(test_text)
        self.assertEqual(cleaned, "")
        processed = self.processor.process_article(test_text)
        self.assertEqual(processed, "")

    def test_non_english_text(self):
        """Test text cleaning with non-English text"""
        test_text = "这是一个测试。これはテストです。Это тест."
        cleaned = self.processor.clean_text(test_text)
        # Should keep non-English characters, but may not process them further
        self.assertTrue(len(cleaned) > 0)
        processed = self.processor.process_article(test_text)
        self.assertTrue(isinstance(processed, str))

    def test_whitespace_only(self):
        """Test text cleaning with whitespace-only input"""
        test_text = "   \t  \n  "
        cleaned = self.processor.clean_text(test_text)
        self.assertEqual(cleaned, "")
        processed = self.processor.process_article(test_text)
        self.assertEqual(processed, "")

def run_tests():
    """Run the test suite"""
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTextProcessor)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success/failure
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Running TextProcessor unit tests...")
    success = run_tests()
    
    if success:
        print("\n🎉 All TextProcessor tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some TextProcessor tests failed!")
        sys.exit(1) 