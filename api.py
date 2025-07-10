from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Path
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import datetime

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

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./news_analysis.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    period_type = Column(String, index=True)  # 'day', 'week', 'month'
    data = Column(Text)  # JSON-encoded graph data

Base.metadata.create_all(bind=engine)

# Add index to date column for performance
Index('ix_snapshots_date', Snapshot.date)

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
    # Save snapshot to database
    db = SessionLocal()
    try:
        # Convert result to JSON-serializable format
        def convert_timestamps(obj):
            if isinstance(obj, dict):
                return {str(k) if hasattr(k, 'strftime') else k: convert_timestamps(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamps(item) for item in obj]
            elif hasattr(obj, 'strftime'):  # Timestamp objects
                return str(obj)
            else:
                return obj
        
        serializable_result = convert_timestamps(result)
        
        snapshot = Snapshot(
            date=datetime.date.today(),
            period_type='day',
            data=json.dumps(serializable_result)
        )
        db.add(snapshot)
        db.commit()
    except Exception as e:
        print(f"Error saving snapshot: {e}")
        # Continue without saving snapshot if there's an error
    finally:
        db.close()
    
    # Also convert the return result to be JSON serializable
    return convert_timestamps(result)

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

@app.get("/snapshots/day/{date}", summary="Get snapshot for a specific day (YYYY-MM-DD)")
def get_snapshot_day(date: str):
    db = SessionLocal()
    try:
        snapshot = db.query(Snapshot).filter(Snapshot.date == date, Snapshot.period_type == 'day').order_by(Snapshot.id.desc()).first()
        if snapshot:
            return json.loads(snapshot.data)
        else:
            raise HTTPException(status_code=404, detail="No snapshot found for this day.")
    finally:
        db.close()

@app.get("/snapshots/week/{year_week}", summary="Get snapshot for a specific week (YYYY-WW)")
def get_snapshot_week(year_week: str = Path(..., description="Format: YYYY-WW, e.g. 2024-25")):
    db = SessionLocal()
    try:
        year, week = map(int, year_week.split('-'))
        # Use the same week calculation as isocalendar()
        from datetime import datetime as dt, timedelta
        
        # Find a date in the requested week
        # Start with January 1st and find the first day of the requested week
        jan1 = dt(year, 1, 1)
        # Find the first Thursday of the year (ISO week 1 contains January 4th)
        while jan1.weekday() != 3:  # Thursday is 3
            jan1 += timedelta(days=1)
        # Go back to Monday of that week
        jan1 -= timedelta(days=3)
        # Calculate the first day of the requested week
        first_day = jan1 + timedelta(weeks=week-1)
        last_day = first_day + timedelta(days=6)
        
        # Get all snapshots in the date range
        all_snapshots = db.query(Snapshot).filter(Snapshot.date >= first_day.date(), Snapshot.date <= last_day.date(), Snapshot.period_type == 'day').all()
        
        if not all_snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found for this week.")
        
        # Aggregate data from all snapshots in the week
        aggregated_keywords = {}
        aggregated_source_counts = {}
        aggregated_source_sentiments = {}
        all_articles = []
        all_temporal_trends = {}
        
        for snapshot in all_snapshots:
            snapshot_data = json.loads(snapshot.data)
            
            # Aggregate keywords
            if 'top_keywords' in snapshot_data:
                for keyword, count in snapshot_data['top_keywords'].items():
                    aggregated_keywords[keyword] = aggregated_keywords.get(keyword, 0) + count
            
            # Aggregate source trends
            if 'source_trends' in snapshot_data:
                if 'article_counts' in snapshot_data['source_trends']:
                    for source, count in snapshot_data['source_trends']['article_counts'].items():
                        aggregated_source_counts[source] = aggregated_source_counts.get(source, 0) + count
                
                if 'sentiment_by_source' in snapshot_data['source_trends']:
                    for source, sentiment in snapshot_data['source_trends']['sentiment_by_source'].items():
                        if source not in aggregated_source_sentiments:
                            aggregated_source_sentiments[source] = []
                        aggregated_source_sentiments[source].append(sentiment)
            
            # Collect articles
            if 'articles' in snapshot_data:
                all_articles.extend(snapshot_data['articles'])
            
            # Collect temporal trends
            if 'temporal_trends' in snapshot_data:
                all_temporal_trends.update(snapshot_data['temporal_trends'])
        
        # Calculate average sentiment by source
        for source in aggregated_source_sentiments:
            if aggregated_source_sentiments[source]:
                aggregated_source_sentiments[source] = sum(aggregated_source_sentiments[source]) / len(aggregated_source_sentiments[source])
        
        # Sort keywords by count
        sorted_keywords = dict(sorted(aggregated_keywords.items(), key=lambda x: x[1], reverse=True)[:10])
        
        aggregated_result = {
            "message": f"News analysis for week {year_week}",
            "top_keywords": sorted_keywords,
            "source_trends": {
                'article_counts': aggregated_source_counts,
                'sentiment_by_source': aggregated_source_sentiments
            },
            "temporal_trends": all_temporal_trends,
            "plot_files": [
                "trend_plots/sentiment_by_source.png",
                "trend_plots/source_distribution.png", 
                "trend_plots/temporal_trends.png",
                "trend_plots/wordcloud.png"
            ],
            "articles": all_articles
        }
        
        return aggregated_result
    finally:
        db.close()

@app.get("/snapshots/month/{year_month}", summary="Get snapshot for a specific month (YYYY-MM)")
def get_snapshot_month(year_month: str = Path(..., description="Format: YYYY-MM, e.g. 2024-06")):
    db = SessionLocal()
    try:
        year, month = map(int, year_month.split('-'))
        from datetime import date
        from calendar import monthrange
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        
        # Get all snapshots in the date range
        all_snapshots = db.query(Snapshot).filter(Snapshot.date >= first_day, Snapshot.date <= last_day, Snapshot.period_type == 'day').all()
        
        if not all_snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found for this month.")
        
        # Aggregate data from all snapshots in the month
        aggregated_keywords = {}
        aggregated_source_counts = {}
        aggregated_source_sentiments = {}
        all_articles = []
        all_temporal_trends = {}
        
        for snapshot in all_snapshots:
            snapshot_data = json.loads(snapshot.data)
            
            # Aggregate keywords
            if 'top_keywords' in snapshot_data:
                for keyword, count in snapshot_data['top_keywords'].items():
                    aggregated_keywords[keyword] = aggregated_keywords.get(keyword, 0) + count
            
            # Aggregate source trends
            if 'source_trends' in snapshot_data:
                if 'article_counts' in snapshot_data['source_trends']:
                    for source, count in snapshot_data['source_trends']['article_counts'].items():
                        aggregated_source_counts[source] = aggregated_source_counts.get(source, 0) + count
                
                if 'sentiment_by_source' in snapshot_data['source_trends']:
                    for source, sentiment in snapshot_data['source_trends']['sentiment_by_source'].items():
                        if source not in aggregated_source_sentiments:
                            aggregated_source_sentiments[source] = []
                        aggregated_source_sentiments[source].append(sentiment)
            
            # Collect articles
            if 'articles' in snapshot_data:
                all_articles.extend(snapshot_data['articles'])
            
            # Collect temporal trends
            if 'temporal_trends' in snapshot_data:
                all_temporal_trends.update(snapshot_data['temporal_trends'])
        
        # Calculate average sentiment by source
        for source in aggregated_source_sentiments:
            if aggregated_source_sentiments[source]:
                aggregated_source_sentiments[source] = sum(aggregated_source_sentiments[source]) / len(aggregated_source_sentiments[source])
        
        # Sort keywords by count
        sorted_keywords = dict(sorted(aggregated_keywords.items(), key=lambda x: x[1], reverse=True)[:10])
        
        aggregated_result = {
            "message": f"News analysis for month {year_month}",
            "top_keywords": sorted_keywords,
            "source_trends": {
                'article_counts': aggregated_source_counts,
                'sentiment_by_source': aggregated_source_sentiments
            },
            "temporal_trends": all_temporal_trends,
            "plot_files": [
                "trend_plots/sentiment_by_source.png",
                "trend_plots/source_distribution.png", 
                "trend_plots/temporal_trends.png",
                "trend_plots/wordcloud.png"
            ],
            "articles": all_articles
        }
        
        return aggregated_result
    finally:
        db.close()

# Utility endpoint to seed the database with fake historical snapshots for testing
@app.post("/seed_snapshots", summary="Seed the database with fake historical snapshots for testing")
def seed_snapshots():
    db = SessionLocal()
    import random
    import pandas as pd
    from datetime import timedelta
    
    # Clear existing snapshots
    db.query(Snapshot).delete()
    
    today = datetime.date.today()
    
    # Realistic news keywords and sources for the past 7 days (excluding today)
    realistic_keywords = [
        {"ukraine": 25, "russia": 22, "war": 18, "kyiv": 15, "nato": 12, "sanctions": 10, "peace": 8, "talks": 7, "military": 6, "europe": 5},
        {"ai": 30, "chatgpt": 25, "technology": 20, "microsoft": 15, "google": 12, "artificial": 10, "intelligence": 8, "innovation": 7, "future": 6, "development": 5},
        {"climate": 28, "global": 22, "warming": 18, "environment": 15, "carbon": 12, "emissions": 10, "green": 8, "energy": 7, "sustainable": 6, "planet": 5},
        {"economy": 26, "inflation": 23, "fed": 18, "interest": 15, "rates": 12, "market": 10, "stocks": 8, "financial": 7, "growth": 6, "recession": 5},
        {"covid": 24, "pandemic": 20, "vaccine": 16, "health": 14, "cases": 12, "hospital": 10, "medical": 8, "treatment": 7, "recovery": 6, "outbreak": 5},
        {"election": 27, "politics": 22, "vote": 18, "campaign": 15, "democratic": 12, "republican": 10, "president": 8, "government": 7, "policy": 6, "debate": 5},
        {"space": 25, "nasa": 20, "mars": 16, "rocket": 14, "satellite": 12, "mission": 10, "astronaut": 8, "exploration": 7, "launch": 6, "orbit": 5}
    ]
    
    realistic_sources = ["BBC", "CNN", "Reuters", "Associated Press", "The Guardian", "New York Times", "Washington Post", "USA Today", "Fox News", "MSNBC"]
    
    # Create realistic snapshots for the past 7 days (including today)
    for days_ago in range(0, 8):  # Start from 0 to include today
        date = today - timedelta(days=days_ago)
        
        # Select realistic keywords for this day
        day_keywords = realistic_keywords[days_ago % len(realistic_keywords)]
        
        # Create realistic source trends
        source_counts = {}
        source_sentiments = {}
        total_articles = 0
        
        for source in realistic_sources[:6]:  # Use first 6 sources
            article_count = random.randint(8, 25)
            source_counts[source] = article_count
            total_articles += article_count
            # Vary sentiment based on source (some sources tend to be more positive/negative)
            if source in ["BBC", "Reuters"]:
                sentiment = random.uniform(-0.1, 0.1)  # More neutral
            elif source in ["Fox News", "MSNBC"]:
                sentiment = random.uniform(-0.3, 0.3)  # More polarized
            else:
                sentiment = random.uniform(-0.2, 0.2)  # Standard range
            source_sentiments[source] = round(sentiment, 3)
        
        # Create realistic temporal trends
        temporal_trends = {}
        for i in range(7):
            trend_date = date - timedelta(days=i)
            if trend_date <= today:
                temporal_trends[str(trend_date)] = random.randint(15, 35)
        
        fake_result = {
            "message": f"News analysis for {date}",
            "top_keywords": day_keywords,
            "source_trends": {
                'article_counts': source_counts,
                'sentiment_by_source': source_sentiments
            },
            "temporal_trends": temporal_trends,
            "plot_files": [
                "trend_plots/sentiment_by_source.png",
                "trend_plots/source_distribution.png", 
                "trend_plots/temporal_trends.png",
                "trend_plots/wordcloud.png"
            ],
            "articles": [
                {
                    "title": f"Sample article {i+1} for {date}",
                    "source": random.choice(realistic_sources),
                    "text": f"This is a sample news article about {list(day_keywords.keys())[0]} for {date}.",
                    "url": f"https://example.com/article-{i+1}",
                    "date": str(date),
                    "sentiment_polarity": random.uniform(-0.5, 0.5)
                }
                for i in range(random.randint(5, 12))
            ]
        }
        
        snapshot = Snapshot(
            date=date,
            period_type='day',
            data=json.dumps(fake_result)
        )
        db.add(snapshot)
    
    db.commit()
    db.close()
    return {"message": "Seeded 7 days of realistic fake snapshots (including today)."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 