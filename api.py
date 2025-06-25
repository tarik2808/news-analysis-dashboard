from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import os
from fastapi.middleware.cors import CORSMiddleware

from news_scraper import NewsScraper
from text_processor import TextProcessor
from trend_analyzer import TrendAnalyzer
from nlp_analyzer_simple import SimpleNLPAnalyzer

# Try to import spaCy-based analyzer
try:
    from nlp_analyzer import NLPAnalyzer
    SPACY_AVAILABLE = True
except ImportError:
    NLPAnalyzer = None
    SPACY_AVAILABLE = False

app = FastAPI(title="News Analysis API", description="API for scraping, processing, analyzing, and trending news articles.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ScrapeRequest(BaseModel):
    articles_per_source: int = 5

class TextProcessRequest(BaseModel):
    texts: List[str]

class AnalyzeRequest(BaseModel):
    texts: List[str]
    pipeline: str = Query('simple', enum=['simple', 'full'], description="Choose 'simple' (TextBlob) or 'full' (spaCy) NLP pipeline.")

class TrendsRequest(BaseModel):
    # Accepts a list of articles with required fields
    source: List[str]
    title: List[str]
    text: List[str]
    url: List[str]
    date: List[str]
    keywords: Optional[List[dict]] = None
    sentiment_polarity: Optional[List[float]] = None

# Endpoints
@app.post("/scrape", summary="Scrape news articles from all sources")
def scrape_news(req: ScrapeRequest):
    scraper = NewsScraper()
    df = scraper.scrape_all_sources(articles_per_source=req.articles_per_source)
    df.to_csv('scraped_articles.csv', index=False)
    return {"message": f"Scraped {len(df)} articles", "articles": df.to_dict(orient='records')}  # Return all articles

@app.post("/process", summary="Process and clean a list of texts")
def process_texts(req: TextProcessRequest):
    processor = TextProcessor()
    processed = [processor.clean_text(t) for t in req.texts]
    return {"processed_texts": processed}

@app.post("/analyze", summary="Analyze texts for sentiment, keywords, and entities")
def analyze_texts(req: AnalyzeRequest):
    if req.pipeline == 'full':
        if not SPACY_AVAILABLE:
            raise HTTPException(status_code=503, detail="spaCy pipeline not available on this environment.")
        analyzer = NLPAnalyzer()
    else:
        analyzer = SimpleNLPAnalyzer()
    results = [analyzer.analyze_article(t) for t in req.texts]
    return {"results": results}

@app.post("/trends", summary="Analyze trends from article data")
def analyze_trends(req: TrendsRequest):
    try:
        print(f"📊 Processing trends for {len(req.source)} articles")
        df = pd.DataFrame({
            'source': req.source,
            'title': req.title,
            'text': req.text,
            'url': req.url,
            'date': req.date,
            'keywords': req.keywords if req.keywords else [{}]*len(req.source),
            'sentiment_polarity': req.sentiment_polarity if req.sentiment_polarity else [0.0]*len(req.source)
        })
        print(f"✅ DataFrame created with shape: {df.shape}")
        print(f"📅 Date range: {df['date'].min()} to {df['date'].max()}")
        trend_analyzer = TrendAnalyzer()
        print("🔍 Extracting keywords...")
        keywords = trend_analyzer.extract_trending_keywords(df)
        print(f"✅ Found {len(keywords)} keywords")
        print("📈 Analyzing source trends...")
        source_trends = trend_analyzer.analyze_source_trends(df)
        print(f"✅ Source trends analyzed")
        print("⏰ Analyzing temporal trends...")
        # Robust date parsing (let pandas infer format)
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        except Exception as e:
            print(f"[ERROR] Date parsing failed: {e}")
        temporal_trends = trend_analyzer.analyze_temporal_trends(df)
        print(f"✅ Temporal trends analyzed")
        print("📊 Generating trend plots...")
        trend_analyzer.plot_trends(df)
        print(f"✅ Trend plots generated")
        result = {
            "top_keywords": keywords,
            "source_trends": {
                'article_counts': source_trends['article_counts'].to_dict(),
                'sentiment_by_source': source_trends['sentiment_by_source'].to_dict()
            },
            "temporal_trends": temporal_trends.to_dict()
        }
        print("🎉 Trends analysis completed successfully")
        return result
    except Exception as e:
        print(f"❌ Error in trends analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@app.post("/full_pipeline", summary="Run the full pipeline: scrape, analyze, trends, plots")
def full_pipeline(req: ScrapeRequest):
    scraper = NewsScraper()
    df = scraper.scrape_all_sources(articles_per_source=req.articles_per_source)
    df.to_csv('scraped_articles.csv', index=False)
    texts = df['text'].tolist()
    analyzer = SimpleNLPAnalyzer()
    analysis = [analyzer.analyze_article(t) for t in texts]
    df['sentiment_polarity'] = [a.get('sentiment', {}).get('polarity', 0.0) for a in analysis]
    df['keywords'] = [a.get('keywords', {}) for a in analysis]
    df.to_csv('analyzed_articles.csv', index=False)
    trend_analyzer = TrendAnalyzer()
    keywords = trend_analyzer.extract_trending_keywords(df)
    source_trends = trend_analyzer.analyze_source_trends(df)
    try:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    except Exception as e:
        print(f"[ERROR] Date parsing failed: {e}")
    temporal_trends = trend_analyzer.analyze_temporal_trends(df)
    trend_analyzer.plot_trends(df)
    result = {
        "message": f"Full pipeline completed for {len(df)} articles.",
        "top_keywords": keywords,
        "source_trends": {
            'article_counts': source_trends['article_counts'].to_dict(),
            'sentiment_by_source': source_trends['sentiment_by_source'].to_dict()
        },
        "temporal_trends": temporal_trends.to_dict(),
        "plot_files": [
            "trend_plots/sentiment_by_source.png",
            "trend_plots/source_distribution.png",
            "trend_plots/temporal_trends.png",
            "trend_plots/wordcloud.png"
        ],
        "articles": df.to_dict(orient="records")
    }
    return result

@app.get("/download/{filename}", summary="Download a result file (CSV or plot)")
def download_file(filename: str):
    allowed_dirs = ['.', './trend_plots', './data']
    for d in allowed_dirs:
        path = os.path.join(d, filename)
        if os.path.isfile(path):
            return FileResponse(path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Welcome to the News Analysis API! See /docs for Swagger UI."} 