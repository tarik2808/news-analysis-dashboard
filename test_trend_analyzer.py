import unittest
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from trend_analyzer import TrendAnalyzer

class TestTrendAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TrendAnalyzer()
        # Create mock data
        self.mock_data = {
            'date': [datetime(2024, 6, 17), datetime(2024, 6, 17), datetime(2024, 6, 18)],
            'source': ['CNN', 'BBC', 'CNN'],
            'keywords': [
                {'apple': 2, 'iphone': 1, 'tesla': 1},
                {'microsoft': 1, 'windows': 2},
                {'apple': 1, 'tesla': 2}
            ],
            'sentiment_polarity': [0.1, -0.2, 0.3]
        }
        self.df = pd.DataFrame(self.mock_data)

    def test_extract_trending_keywords(self):
        keywords = self.analyzer.extract_trending_keywords(self.df, top_n=3)
        self.assertIn('apple', keywords)
        self.assertIn('iphone', keywords)
        self.assertIn('tesla', keywords)
        self.assertEqual(keywords['apple'], 2)  # apple appears in two articles

    def test_analyze_temporal_trends(self):
        trends = self.analyzer.analyze_temporal_trends(self.df)
        self.assertEqual(trends.iloc[0], 2)  # 2 articles on 2024-06-17
        self.assertEqual(trends.iloc[1], 1)  # 1 article on 2024-06-18

    def test_analyze_source_trends(self):
        source_trends = self.analyzer.analyze_source_trends(self.df)
        self.assertIn('CNN', source_trends['article_counts'])
        self.assertIn('BBC', source_trends['article_counts'])
        self.assertEqual(source_trends['article_counts']['CNN'], 2)
        self.assertEqual(source_trends['article_counts']['BBC'], 1)
        self.assertAlmostEqual(source_trends['sentiment_by_source']['CNN'], 0.2)
        self.assertAlmostEqual(source_trends['sentiment_by_source']['BBC'], -0.2)

    def test_generate_wordcloud(self):
        output_file = 'test_wordcloud.png'
        self.analyzer.generate_wordcloud(self.df, output_file=output_file)
        self.assertTrue(os.path.exists(output_file))
        os.remove(output_file)

    def test_plot_trends(self):
        output_dir = 'test_trend_plots'
        self.analyzer.plot_trends(self.df, output_dir=output_dir)
        expected_files = [
            'temporal_trends.png',
            'source_distribution.png',
            'sentiment_by_source.png',
            'wordcloud.png'
        ]
        for fname in expected_files:
            fpath = os.path.join(output_dir, fname)
            self.assertTrue(os.path.exists(fpath))
            os.remove(fpath)
        os.rmdir(output_dir)

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=self.df.columns)
        keywords = self.analyzer.extract_trending_keywords(empty_df)
        self.assertEqual(keywords, {})
        trends = self.analyzer.analyze_source_trends(empty_df)
        self.assertTrue('article_counts' in trends)
        self.assertTrue(trends['article_counts'].empty)

if __name__ == '__main__':
    unittest.main() 