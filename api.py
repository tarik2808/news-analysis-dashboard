from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Path, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import pandas as pd
import os
import csv
import io
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, Index, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import datetime
from itsdangerous import URLSafeTimedSerializer
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# Newsletter config
BASE_URL = "http://localhost:8000"  # Change to your public URL if needed
SECRET_KEY = "your-very-secret-key"  # Set a strong secret key
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Mailgun SMTP configuration (use environment variables for security)
MAILGUN_SMTP_HOST = os.getenv("MAILGUN_SMTP_HOST", "smtp.eu.mailgun.org")
MAILGUN_SMTP_PORT = int(os.getenv("MAILGUN_SMTP_PORT", "587"))
MAILGUN_SMTP_USERNAME = os.getenv("MAILGUN_SMTP_USERNAME", "postmaster@mg.tarikcoralic.me")
MAILGUN_SMTP_PASSWORD = os.getenv("MAILGUN_SMTP_PASSWORD", "")  # Set this via environment variable
MAILGUN_FROM_EMAIL = os.getenv("MAILGUN_FROM_EMAIL", "postmaster@mg.tarikcoralic.me")
MAILGUN_FROM_NAME = os.getenv("MAILGUN_FROM_NAME", "SDP Project Tarik Coralic")

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

# Add NewsletterSignup model for newsletter endpoint
class NewsletterSignup(BaseModel):
    email: str

# Add NewsletterDelete model for newsletter deletion
class NewsletterDelete(BaseModel):
    email: str

# Newsletter subscriber model for newsletter signup/verification

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./news_analysis.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Place the model here, after Base is defined:
class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    email = Column(String, primary_key=True, index=True)
    token = Column(String)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    
    result = {
        "message": f"Full pipeline completed for {len(df)} articles.",
        "top_keywords": keywords,
        "source_trends": {
            'article_counts': source_trends['article_counts'].to_dict(),
            'sentiment_by_source': source_trends['sentiment_by_source'].to_dict()
        },
        "temporal_trends": convert_timestamps(temporal_trends.to_dict()),
        "plot_files": [
            "trend_plots/sentiment_by_source.png",
            "trend_plots/source_distribution.png",
            "trend_plots/temporal_trends.png",
            "trend_plots/wordcloud.png"
        ],
        "articles": convert_timestamps(df.to_dict(orient="records"))
    }
    
    # Save snapshot to database for time-based filtering
    db = SessionLocal()
    try:
        # Create today's snapshot
        today = datetime.datetime.now().date()
        
        # Check if snapshot already exists for today
        existing_snapshot = db.query(Snapshot).filter(
            Snapshot.date == today,
            Snapshot.period_type == 'day'
        ).first()
        
        if existing_snapshot:
            # Update existing snapshot
            existing_snapshot.data = json.dumps(result)
            db.commit()
            print(f"Updated snapshot for {today}")
        else:
            # Create new snapshot
            snapshot = Snapshot(
                date=today,
                period_type='day',
                data=json.dumps(result)
            )
            db.add(snapshot)
            db.commit()
            print(f"Created new snapshot for {today}")
            
    except Exception as e:
        print(f"Database save error: {e}")
        db.rollback()
    finally:
        db.close()
    
    return result

@app.post("/full_pipeline_stream", summary="Run the full pipeline with real-time progress streaming")
def full_pipeline_stream(req: ScrapeRequest):
    """Run the full pipeline with real-time progress updates via Server-Sent Events"""
    import time
    import json
    
    def generate_progress():
        try:
            # Step 1: Scraping (15% of total progress)
            yield f"data: {json.dumps({'step': 'Scraping news articles...', 'progress': 5, 'status': 'running'})}\n\n"
            scraper = NewsScraper()
            df = scraper.scrape_all_sources(articles_per_source=req.articles_per_source)
            df.to_csv('scraped_articles.csv', index=False)
            yield f"data: {json.dumps({'step': 'Articles scraped successfully', 'progress': 15, 'status': 'running'})}\n\n"
            
            # Step 2: Text processing (5% of total progress)
            yield f"data: {json.dumps({'step': 'Processing article text...', 'progress': 20, 'status': 'running'})}\n\n"
            texts = df['text'].tolist()
            
            # Step 3: Sentiment analysis (60% of total progress - this is the longest step)
            yield f"data: {json.dumps({'step': 'Analyzing sentiment...', 'progress': 25, 'status': 'running'})}\n\n"
            analyzer = SimpleNLPAnalyzer()
            analysis = []
            total_texts = len(texts)
            
            for i, text in enumerate(texts):
                analysis.append(analyzer.analyze_article(text))
                # Update progress based on sentiment analysis completion
                progress = 25 + int((i + 1) / total_texts * 60)
                yield f"data: {json.dumps({'step': f'Analyzing sentiment... ({i+1}/{total_texts})', 'progress': progress, 'status': 'running'})}\n\n"
                time.sleep(0.05)  # Small delay for better UX
            
            df['sentiment_polarity'] = [a.get('sentiment', {}).get('polarity', 0.0) for a in analysis]
            df['keywords'] = [a.get('keywords', {}) for a in analysis]
            df.to_csv('analyzed_articles.csv', index=False)
            
            # Step 4: Trend analysis (15% of total progress)
            yield f"data: {json.dumps({'step': 'Extracting keywords...', 'progress': 85, 'status': 'running'})}\n\n"
            trend_analyzer = TrendAnalyzer()
            keywords = trend_analyzer.extract_trending_keywords(df)
            yield f"data: {json.dumps({'step': 'Generating trends...', 'progress': 90, 'status': 'running'})}\n\n"
            source_trends = trend_analyzer.analyze_source_trends(df)
            
            # Step 5: Temporal analysis and plotting (5% of total progress)
            yield f"data: {json.dumps({'step': 'Creating visualizations...', 'progress': 95, 'status': 'running'})}\n\n"
            try:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            except Exception as e:
                print(f"[ERROR] Date parsing failed: {e}")
            temporal_trends = trend_analyzer.analyze_temporal_trends(df)
            trend_analyzer.plot_trends(df)
            
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
            
            # Final result
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
            
            # Convert all timestamps in the result
            result = convert_timestamps(result)
            
            # Split the result into smaller chunks to avoid JSON truncation
            # Send metadata first
            metadata = {
                "message": result["message"],
                "top_keywords": result["top_keywords"],
                "source_trends": result["source_trends"],
                "temporal_trends": result["temporal_trends"],
                "plot_files": result["plot_files"],
                "article_count": len(result["articles"])
            }
            
            yield f"data: {json.dumps({'step': 'Finalizing results...', 'progress': 98, 'status': 'running'})}\n\n"
            
            # Send metadata first
            yield f"data: {json.dumps({'step': 'Sending analysis results...', 'progress': 99, 'status': 'running', 'metadata': metadata})}\n\n"
            
            # Send articles in smaller chunks
            articles = result["articles"]
            chunk_size = 10  # Send 10 articles at a time
            for i in range(0, len(articles), chunk_size):
                chunk = articles[i:i + chunk_size]
                yield f"data: {json.dumps({'step': f'Sending articles {i+1}-{min(i+chunk_size, len(articles))}...', 'progress': 99, 'status': 'running', 'articles_chunk': chunk})}\n\n"
                time.sleep(0.01)  # Small delay between chunks
            
            # Send final completion with all data
            yield f"data: {json.dumps({'step': 'Pipeline completed!', 'progress': 100, 'status': 'completed', 'result': result})}\n\n"
            
            # Save snapshot to database
            db = SessionLocal()
            try:
                # Create today's snapshot
                today = datetime.datetime.now().date()
                
                # Check if snapshot already exists for today
                existing_snapshot = db.query(Snapshot).filter(
                    Snapshot.date == today,
                    Snapshot.period_type == 'day'
                ).first()
                
                if existing_snapshot:
                    # Update existing snapshot
                    existing_snapshot.data = json.dumps(result)
                    db.commit()
                    print(f"Updated snapshot for {today}")
                else:
                    # Create new snapshot
                    snapshot = Snapshot(
                        date=today,
                        period_type='day',
                        data=json.dumps(result)
                    )
                    db.add(snapshot)
                    db.commit()
                    print(f"Created new snapshot for {today}")
                    
            except Exception as e:
                print(f"Database save error: {e}")
                db.rollback()
            finally:
                db.close()
            
            # Send completion message
            yield f"data: {json.dumps({'step': 'Pipeline completed!', 'progress': 100, 'status': 'completed', 'result': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'step': 'Pipeline failed', 'progress': 0, 'status': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/plain")

@app.get("/download/{filename}", summary="Download a result file (CSV or plot)")
def download_file(filename: str):
    allowed_dirs = ['.', './trend_plots', './data']
    for d in allowed_dirs:
        path = os.path.join(d, filename)
        if os.path.isfile(path):
            return FileResponse(path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/export/articles", summary="Export analyzed articles as Excel-compatible CSV")
def export_articles_csv():
    """Export all analyzed articles with sentiment scores and metadata in Excel-friendly format"""
    try:
        if not os.path.exists('analyzed_articles.csv'):
            raise HTTPException(status_code=404, detail="No analyzed articles found. Please run analysis first.")
        
        df = pd.read_csv('analyzed_articles.csv')
        
        # Clean and format data for Excel compatibility
        # Convert keywords dict to readable string with proper formatting
        def format_keywords(keywords_str):
            try:
                if isinstance(keywords_str, str) and keywords_str.startswith('{'):
                    keywords_dict = eval(keywords_str)
                    # Sort by frequency and format nicely
                    sorted_keywords = sorted(keywords_dict.items(), key=lambda x: x[1], reverse=True)
                    return '; '.join([f"{k} ({v})" for k, v in sorted_keywords[:20]])  # Top 10 keywords
                return str(keywords_str)
            except:
                return str(keywords_str)
        
        df['keywords'] = df['keywords'].apply(format_keywords)
        
        # Clean text content (remove excessive newlines and special characters)
        df['text'] = df['text'].str.replace('\n', ' ').str.replace('\r', ' ').str.replace('\t', ' ').str.strip()
        df['title'] = df['title'].str.replace('\n', ' ').str.replace('\r', ' ').str.replace('\t', ' ').str.strip()
        
        # Format sentiment polarity as percentage for Excel
        df['sentiment_percentage'] = (df['sentiment_polarity'] * 100).round(2)
        df['sentiment_percentage'] = df['sentiment_percentage'].astype(str) + '%'
        
        # Add sentiment category
        df['sentiment_category'] = df['sentiment_polarity'].apply(
            lambda x: 'Positive' if x > 0.1 else 'Negative' if x < -0.1 else 'Neutral'
        )
        
        # Add word count
        df['word_count'] = df['text'].str.split().str.len()
        
        # Format dates properly for Excel
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Reorder columns for better Excel display
        column_order = ['title', 'source', 'date', 'sentiment_category', 'sentiment_percentage', 
                       'sentiment_polarity', 'word_count', 'keywords', 'text', 'url']
        
        # Only include columns that exist
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        # Ensure all columns are properly formatted
        df = df.fillna('')  # Replace NaN with empty strings
        
        # Create CSV in memory with proper encoding
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel
        output.seek(0)
        
        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment; filename=analyzed_articles_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/sentiment", summary="Export sentiment analysis results as Excel-compatible CSV")
def export_sentiment_csv():
    """Export sentiment analysis summary by source and time in Excel-friendly format"""
    try:
        if not os.path.exists('analyzed_articles.csv'):
            raise HTTPException(status_code=404, detail="No analyzed articles found. Please run analysis first.")
        
        df = pd.read_csv('analyzed_articles.csv')
        
        # Create sentiment summary
        sentiment_summary = []
        
        # Overall sentiment stats
        total_articles = len(df)
        positive_count = len(df[df['sentiment_polarity'] > 0.1])
        negative_count = len(df[df['sentiment_polarity'] < -0.1])
        neutral_count = len(df[(df['sentiment_polarity'] >= -0.1) & (df['sentiment_polarity'] <= 0.1)])
        
        overall_stats = {
            'Analysis_Type': 'Overall Summary',
            'Source': 'All Sources Combined',
            'Total_Articles': total_articles,
            'Average_Sentiment_Score': round(df['sentiment_polarity'].mean(), 3),
            'Average_Sentiment_Percentage': f"{round(df['sentiment_polarity'].mean() * 100, 2)}%",
            'Positive_Articles': positive_count,
            'Positive_Percentage': f"{round((positive_count / total_articles) * 100, 2)}%",
            'Negative_Articles': negative_count,
            'Negative_Percentage': f"{round((negative_count / total_articles) * 100, 2)}%",
            'Neutral_Articles': neutral_count,
            'Neutral_Percentage': f"{round((neutral_count / total_articles) * 100, 2)}%",
            'Highest_Sentiment': round(df['sentiment_polarity'].max(), 3),
            'Lowest_Sentiment': round(df['sentiment_polarity'].min(), 3),
            'Sentiment_Range': f"{round(df['sentiment_polarity'].min(), 3)} to {round(df['sentiment_polarity'].max(), 3)}"
        }
        sentiment_summary.append(overall_stats)
        
        # By source
        for source in df['source'].unique():
            source_df = df[df['source'] == source]
            source_total = len(source_df)
            source_positive = len(source_df[source_df['sentiment_polarity'] > 0.1])
            source_negative = len(source_df[source_df['sentiment_polarity'] < -0.1])
            source_neutral = len(source_df[(source_df['sentiment_polarity'] >= -0.1) & (source_df['sentiment_polarity'] <= 0.1)])
            
            source_stats = {
                'Analysis_Type': 'By Source',
                'Source': source,
                'Total_Articles': source_total,
                'Average_Sentiment_Score': round(source_df['sentiment_polarity'].mean(), 3),
                'Average_Sentiment_Percentage': f"{round(source_df['sentiment_polarity'].mean() * 100, 2)}%",
                'Positive_Articles': source_positive,
                'Positive_Percentage': f"{round((source_positive / source_total) * 100, 2)}%" if source_total > 0 else "0%",
                'Negative_Articles': source_negative,
                'Negative_Percentage': f"{round((source_negative / source_total) * 100, 2)}%" if source_total > 0 else "0%",
                'Neutral_Articles': source_neutral,
                'Neutral_Percentage': f"{round((source_neutral / source_total) * 100, 2)}%" if source_total > 0 else "0%",
                'Highest_Sentiment': round(source_df['sentiment_polarity'].max(), 3),
                'Lowest_Sentiment': round(source_df['sentiment_polarity'].min(), 3),
                'Sentiment_Range': f"{round(source_df['sentiment_polarity'].min(), 3)} to {round(source_df['sentiment_polarity'].max(), 3)}"
            }
            sentiment_summary.append(source_stats)
        
        # Convert to DataFrame and CSV
        summary_df = pd.DataFrame(sentiment_summary)
        
        # Add analysis timestamp
        summary_df['Analysis_Date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        output = io.StringIO()
        summary_df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment; filename=sentiment_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/trends", summary="Export trending keywords and analysis as Excel-compatible CSV")
def export_trends_csv():
    """Export trending keywords and trend analysis results in Excel-friendly format"""
    try:
        if not os.path.exists('analyzed_articles.csv'):
            raise HTTPException(status_code=404, detail="No analyzed articles found. Please run analysis first.")
        
        df = pd.read_csv('analyzed_articles.csv')
        
        # Extract trending keywords from the keywords column
        import ast
        all_keywords = {}
        
        for keywords_str in df['keywords']:
            try:
                if isinstance(keywords_str, str) and keywords_str.startswith('{'):
                    keywords_dict = ast.literal_eval(keywords_str)
                    for keyword, count in keywords_dict.items():
                        if keyword in all_keywords:
                            all_keywords[keyword] += count
                        else:
                            all_keywords[keyword] = count
            except:
                continue
        
        # Convert to DataFrame with proper filtering
        keywords_data = []
        total_articles = len(df)
        total_keyword_mentions = sum(all_keywords.values())
        
        for keyword, count in all_keywords.items():
            # Filter out non-meaningful keywords
            stop_words = [
                'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'oil', 'sit', 'try', 'use', 'she', 'too', 'any', 'ask', 'end', 'far', 'few', 'got', 'let', 'put', 'say',
                'this', 'that', 'with', 'have', 'will', 'been', 'than', 'more', 'also', 'each', 'which', 'their', 'time', 'very', 'when', 'much', 'some', 'these', 'other', 'into', 'only', 'over', 'think', 'also', 'back', 'after', 'first', 'well', 'work', 'life', 'where', 'most', 'even', 'much', 'take', 'here', 'just', 'like', 'long', 'make', 'many', 'such', 'turn', 'want', 'know', 'look', 'right', 'good', 'great', 'little', 'own', 'other', 'old', 'see', 'him', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call', 'who', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part',
                'lafufu', 'brooks', 'ahn', 'kent', 'horres'  # Remove specific problematic words
            ]
            
            if (isinstance(keyword, str) and 
                len(keyword) > 2 and 
                len(keyword) < 20 and  # Avoid very long words
                not keyword.startswith('{') and 
                not keyword.startswith('"') and
                not keyword.isdigit() and
                keyword.lower() not in stop_words and
                keyword.isalpha() and  # Only alphabetic characters
                not keyword.endswith('s') or len(keyword) > 4):  # Avoid single letters with 's'
                
                # Calculate percentage of total keyword mentions (more meaningful)
                percentage = round((count / total_keyword_mentions) * 100, 2)
                keywords_data.append({
                    'Rank': 0,  # Will be filled after sorting
                    'Keyword': keyword.title(),  # Capitalize for better readability
                    'Frequency': count,
                    'Percentage': f"{percentage}%",
                    'Frequency_Per_Article': round(count / total_articles, 3),
                    'Trend_Score': round(count * (count / total_articles), 2),  # Weighted score
                    'Category': 'High' if count >= total_articles * 0.1 else 'Medium' if count >= total_articles * 0.05 else 'Low'
                })
        
        keywords_df = pd.DataFrame(keywords_data)
        keywords_df = keywords_df.sort_values('Frequency', ascending=False)
        
        # Add ranking
        keywords_df['Rank'] = range(1, len(keywords_df) + 1)
        
        # Reorder columns for better Excel display
        keywords_df = keywords_df[['Rank', 'Keyword', 'Frequency', 'Percentage', 'Frequency_Per_Article', 'Trend_Score', 'Category']]
        
        # Add summary statistics
        summary_stats = {
            'Rank': 'SUMMARY',
            'Keyword': f'Total Unique Keywords: {len(keywords_df)}',
            'Frequency': f'Total Mentions: {total_keyword_mentions}',
            'Percentage': f'Average per Keyword: {round(keywords_df["Frequency"].mean(), 2)}',
            'Frequency_Per_Article': f'Most Frequent: {keywords_df.iloc[0]["Keyword"]} ({keywords_df.iloc[0]["Frequency"]} times)',
            'Trend_Score': f'Analysis Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'Category': f'Articles Analyzed: {total_articles}'
        }
        
        # Add summary as first row
        summary_df = pd.DataFrame([summary_stats])
        keywords_df = pd.concat([summary_df, keywords_df], ignore_index=True)
        
        output = io.StringIO()
        keywords_df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment; filename=trending_keywords_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/complete", summary="Export complete analysis report as Excel-compatible CSV")
def export_complete_analysis_csv():
    """Export comprehensive analysis report including articles, sentiment, and trends in Excel-friendly format"""
    try:
        if not os.path.exists('analyzed_articles.csv'):
            raise HTTPException(status_code=404, detail="No analyzed articles found. Please run analysis first.")
        
        df = pd.read_csv('analyzed_articles.csv')
        
        # Clean and format data for Excel compatibility
        def format_keywords(keywords_str):
            try:
                if isinstance(keywords_str, str) and keywords_str.startswith('{'):
                    keywords_dict = eval(keywords_str)
                    sorted_keywords = sorted(keywords_dict.items(), key=lambda x: x[1], reverse=True)
                    return '; '.join([f"{k} ({v})" for k, v in sorted_keywords[:20]])
                return str(keywords_str)
            except:
                return str(keywords_str)
        
        df['keywords'] = df['keywords'].apply(format_keywords)
        
        # Clean text content (remove excessive newlines and special characters)
        df['text'] = df['text'].str.replace('\n', ' ').str.replace('\r', ' ').str.replace('\t', ' ').str.strip()
        df['title'] = df['title'].str.replace('\n', ' ').str.replace('\r', ' ').str.replace('\t', ' ').str.strip()
        
        # Add comprehensive analysis columns
        df['sentiment_category'] = df['sentiment_polarity'].apply(
            lambda x: 'Positive' if x > 0.1 else 'Negative' if x < -0.1 else 'Neutral'
        )
        df['sentiment_strength'] = df['sentiment_polarity'].apply(
            lambda x: 'Strong' if abs(x) > 0.5 else 'Moderate' if abs(x) > 0.2 else 'Weak'
        )
        df['sentiment_percentage'] = (df['sentiment_polarity'] * 100).round(2)
        df['sentiment_percentage'] = df['sentiment_percentage'].astype(str) + '%'
        
        # Add word count and reading time estimation
        df['word_count'] = df['text'].str.split().str.len()
        df['estimated_reading_time_minutes'] = (df['word_count'] / 200).round(1)  # Average 200 words per minute
        
        # Add text analysis metrics
        df['sentence_count'] = df['text'].str.count(r'[.!?]+')
        df['avg_words_per_sentence'] = (df['word_count'] / df['sentence_count']).round(1)
        df['avg_words_per_sentence'] = df['avg_words_per_sentence'].fillna(0)
        
        # Format dates properly for Excel
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add analysis metadata
        df['analysis_timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['analysis_version'] = '1.0'
        
        # Reorder columns for better Excel display
        column_order = [
            'title', 'source', 'date', 'url',
            'sentiment_category', 'sentiment_strength', 'sentiment_percentage', 'sentiment_polarity',
            'word_count', 'sentence_count', 'avg_words_per_sentence', 'estimated_reading_time_minutes',
            'keywords', 'text',
            'analysis_timestamp', 'analysis_version'
        ]
        
        # Only include columns that exist
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        # Ensure all columns are properly formatted
        df = df.fillna('')  # Replace NaN with empty strings
        
        # Create CSV in memory with proper encoding
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment; filename=complete_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/all", summary="Export all analysis data as Excel-compatible CSV")
def export_all_analysis_csv():
    """Export comprehensive analysis including articles, sentiment, trends, and summary statistics"""
    try:
        if not os.path.exists('analyzed_articles.csv'):
            raise HTTPException(status_code=404, detail="No analyzed articles found. Please run analysis first.")
        
        df = pd.read_csv('analyzed_articles.csv')
        
        # Create a comprehensive report with multiple sheets worth of data
        all_data = []
        
        # 1. Article Analysis Data
        def format_keywords(keywords_str):
            try:
                if isinstance(keywords_str, str) and keywords_str.startswith('{'):
                    keywords_dict = eval(keywords_str)
                    sorted_keywords = sorted(keywords_dict.items(), key=lambda x: x[1], reverse=True)
                    return '; '.join([f"{k} ({v})" for k, v in sorted_keywords[:20]])
                return str(keywords_str)
            except:
                return str(keywords_str)
        
        # Clean and format article data
        article_data = df.copy()
        article_data['keywords'] = article_data['keywords'].apply(format_keywords)
        article_data['text'] = article_data['text'].str.replace('\n', ' ').str.replace('\r', ' ').str.replace('\t', ' ').str.strip()
        article_data['title'] = article_data['title'].str.replace('\n', ' ').str.replace('\r', ' ').str.replace('\t', ' ').str.strip()
        
        # Add analysis columns
        article_data['sentiment_category'] = article_data['sentiment_polarity'].apply(
            lambda x: 'Positive' if x > 0.1 else 'Negative' if x < -0.1 else 'Neutral'
        )
        article_data['sentiment_percentage'] = (article_data['sentiment_polarity'] * 100).round(2).astype(str) + '%'
        article_data['word_count'] = article_data['text'].str.split().str.len()
        article_data['estimated_reading_time'] = (article_data['word_count'] / 200).round(1)
        
        # Format dates
        if 'date' in article_data.columns:
            article_data['date'] = pd.to_datetime(article_data['date'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add section identifier
        article_data['Data_Section'] = 'Article Analysis'
        article_data['Analysis_Date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Reorder columns
        article_columns = ['Data_Section', 'title', 'source', 'date', 'sentiment_category', 'sentiment_percentage', 
                          'word_count', 'estimated_reading_time', 'keywords', 'url', 'Analysis_Date']
        existing_article_columns = [col for col in article_columns if col in article_data.columns]
        article_data = article_data[existing_article_columns]
        
        all_data.append(article_data)
        
        # 2. Sentiment Summary Data
        sentiment_summary = []
        total_articles = len(df)
        positive_count = len(df[df['sentiment_polarity'] > 0.1])
        negative_count = len(df[df['sentiment_polarity'] < -0.1])
        neutral_count = len(df[(df['sentiment_polarity'] >= -0.1) & (df['sentiment_polarity'] <= 0.1)])
        
        # Overall summary
        overall_stats = {
            'Data_Section': 'Sentiment Summary',
            'Analysis_Type': 'Overall Summary',
            'Source': 'All Sources Combined',
            'Total_Articles': total_articles,
            'Average_Sentiment_Score': round(df['sentiment_polarity'].mean(), 3),
            'Average_Sentiment_Percentage': f"{round(df['sentiment_polarity'].mean() * 100, 2)}%",
            'Positive_Articles': positive_count,
            'Positive_Percentage': f"{round((positive_count / total_articles) * 100, 2)}%",
            'Negative_Articles': negative_count,
            'Negative_Percentage': f"{round((negative_count / total_articles) * 100, 2)}%",
            'Neutral_Articles': neutral_count,
            'Neutral_Percentage': f"{round((neutral_count / total_articles) * 100, 2)}%",
            'Analysis_Date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        sentiment_summary.append(overall_stats)
        
        # By source
        for source in df['source'].unique():
            source_df = df[df['source'] == source]
            source_total = len(source_df)
            source_positive = len(source_df[source_df['sentiment_polarity'] > 0.1])
            source_negative = len(source_df[source_df['sentiment_polarity'] < -0.1])
            source_neutral = len(source_df[(source_df['sentiment_polarity'] >= -0.1) & (source_df['sentiment_polarity'] <= 0.1)])
            
            source_stats = {
                'Data_Section': 'Sentiment Summary',
                'Analysis_Type': 'By Source',
                'Source': source,
                'Total_Articles': source_total,
                'Average_Sentiment_Score': round(source_df['sentiment_polarity'].mean(), 3),
                'Average_Sentiment_Percentage': f"{round(source_df['sentiment_polarity'].mean() * 100, 2)}%",
                'Positive_Articles': source_positive,
                'Positive_Percentage': f"{round((source_positive / source_total) * 100, 2)}%" if source_total > 0 else "0%",
                'Negative_Articles': source_negative,
                'Negative_Percentage': f"{round((source_negative / source_total) * 100, 2)}%" if source_total > 0 else "0%",
                'Neutral_Articles': source_neutral,
                'Neutral_Percentage': f"{round((source_neutral / source_total) * 100, 2)}%" if source_total > 0 else "0%",
                'Analysis_Date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            sentiment_summary.append(source_stats)
        
        sentiment_df = pd.DataFrame(sentiment_summary)
        all_data.append(sentiment_df)
        
        # 3. Trending Keywords Data
        import ast
        all_keywords = {}
        
        for keywords_str in df['keywords']:
            try:
                if isinstance(keywords_str, str) and keywords_str.startswith('{'):
                    keywords_dict = ast.literal_eval(keywords_str)
                    for keyword, count in keywords_dict.items():
                        if keyword in all_keywords:
                            all_keywords[keyword] += count
                        else:
                            all_keywords[keyword] = count
            except:
                continue
        
        keywords_data = []
        total_keyword_mentions = sum(all_keywords.values())
        for keyword, count in all_keywords.items():
            if (isinstance(keyword, str) and len(keyword) > 2 and len(keyword) < 20 and 
                keyword.isalpha() and keyword.lower() not in ['the', 'and', 'for', 'are', 'but', 'not']):
                
                # Calculate percentage of total keyword mentions (more meaningful)
                percentage = round((count / total_keyword_mentions) * 100, 2)
                keywords_data.append({
                    'Data_Section': 'Trending Keywords',
                    'Rank': 0,  # Will be filled after sorting
                    'Keyword': keyword.title(),
                    'Frequency': count,
                    'Percentage': f"{percentage}%",
                    'Frequency_Per_Article': round(count / total_articles, 3),
                    'Trend_Score': round(count * (count / total_articles), 2),
                    'Category': 'High' if count >= total_articles * 0.1 else 'Medium' if count >= total_articles * 0.05 else 'Low',
                    'Analysis_Date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        keywords_df = pd.DataFrame(keywords_data)
        keywords_df = keywords_df.sort_values('Frequency', ascending=False)
        keywords_df['Rank'] = range(1, len(keywords_df) + 1)
        
        all_data.append(keywords_df)
        
        # Create a cleaner combined report with better structure
        # Add section separators and headers for better readability
        section_separators = []
        
        # Add section headers
        section_separators.append(pd.DataFrame([{
            'Data_Section': '=== ARTICLE ANALYSIS ===',
            'Source': '',
            'Total_Articles': '',
            'Average_Sentiment': '',
            'Average_Sentiment_Percentage': '',
            'Positive_Articles': '',
            'Positive_Percentage': '',
            'Negative_Articles': '',
            'Negative_Percentage': '',
            'Neutral_Articles': '',
            'Neutral_Percentage': '',
            'Analysis_Date': ''
        }]))
        
        # Add articles data
        section_separators.append(article_data)
        
        # Add sentiment section header
        section_separators.append(pd.DataFrame([{
            'Data_Section': '=== SENTIMENT SUMMARY ===',
            'Source': '',
            'Total_Articles': '',
            'Average_Sentiment': '',
            'Average_Sentiment_Percentage': '',
            'Positive_Articles': '',
            'Positive_Percentage': '',
            'Negative_Articles': '',
            'Negative_Percentage': '',
            'Neutral_Articles': '',
            'Neutral_Percentage': '',
            'Analysis_Date': ''
        }]))
        
        # Add sentiment data
        section_separators.append(sentiment_df)
        
        # Add trends section header
        section_separators.append(pd.DataFrame([{
            'Data_Section': '=== TRENDING KEYWORDS ===',
            'Source': '',
            'Total_Articles': '',
            'Average_Sentiment': '',
            'Average_Sentiment_Percentage': '',
            'Positive_Articles': '',
            'Positive_Percentage': '',
            'Negative_Articles': '',
            'Negative_Percentage': '',
            'Neutral_Articles': '',
            'Neutral_Percentage': '',
            'Analysis_Date': ''
        }]))
        
        # Add trends data
        section_separators.append(keywords_df)
        
        # Combine all data with separators
        combined_df = pd.concat(section_separators, ignore_index=True)
        
        # Create CSV in memory with proper encoding
        output = io.StringIO()
        combined_df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv; charset=utf-8-sig",
            headers={"Content-Disposition": f"attachment; filename=complete_news_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

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

@app.get("/snapshots/rolling-week/{date}", summary="Get rolling 7-day period ending on date (YYYY-MM-DD)")
def get_rolling_week(date: str):
    """Get aggregated data for the past 7 days ending on the specified date"""
    db = SessionLocal()
    try:
        from datetime import datetime as dt, timedelta
        
        # Parse the end date
        end_date = dt.strptime(date, '%Y-%m-%d').date()
        start_date = end_date - timedelta(days=6)  # 7 days total including end_date
        
        # Get all snapshots in the rolling 7-day period
        all_snapshots = db.query(Snapshot).filter(
            Snapshot.date >= start_date, 
            Snapshot.date <= end_date, 
            Snapshot.period_type == 'day'
        ).all()
        
        if not all_snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found for this 7-day period.")
        
        # Aggregate data from all snapshots in the period
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
        
        # Sort keywords by count - show more keywords for longer periods
        sorted_keywords = dict(sorted(aggregated_keywords.items(), key=lambda x: x[1], reverse=True)[:20])
        
        aggregated_result = {
            "message": f"News analysis for rolling 7-day period ending {date}",
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
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rolling week data: {str(e)}")
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
        sorted_keywords = dict(sorted(aggregated_keywords.items(), key=lambda x: x[1], reverse=True)[:20])
        
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

@app.get("/snapshots/rolling-month/{date}", summary="Get rolling 30-day period ending on date (YYYY-MM-DD)")
def get_rolling_month(date: str):
    """Get aggregated data for the past 30 days ending on the specified date"""
    db = SessionLocal()
    try:
        from datetime import datetime as dt, timedelta
        
        # Parse the end date
        end_date = dt.strptime(date, '%Y-%m-%d').date()
        start_date = end_date - timedelta(days=29)  # 30 days total including end_date
        
        # Get all snapshots in the rolling 30-day period
        all_snapshots = db.query(Snapshot).filter(
            Snapshot.date >= start_date, 
            Snapshot.date <= end_date, 
            Snapshot.period_type == 'day'
        ).all()
        
        if not all_snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found for this 30-day period.")
        
        # Aggregate data from all snapshots in the period
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
        
        # Sort keywords by count - show more keywords for longer periods
        sorted_keywords = dict(sorted(aggregated_keywords.items(), key=lambda x: x[1], reverse=True)[:30])
        
        aggregated_result = {
            "message": f"News analysis for rolling 30-day period ending {date}",
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
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving rolling month data: {str(e)}")
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
        sorted_keywords = dict(sorted(aggregated_keywords.items(), key=lambda x: x[1], reverse=True)[:20])
        
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

@app.post("/snapshots/generate_weekly", summary="Generate a weekly snapshot from the last 7 days")
def generate_weekly_snapshot():
    db = SessionLocal()
    try:
        from datetime import date, timedelta
        today = date.today()
        week_start = today - timedelta(days=6)
        # Get all daily snapshots for the last 7 days
        daily_snaps = db.query(Snapshot).filter(
            Snapshot.period_type == 'day',
            Snapshot.date >= week_start,
            Snapshot.date <= today
        ).all()
        if not daily_snaps:
            return {"message": "No daily snapshots found for the last 7 days."}
        # Aggregate data
        articles = []
        keywords = {}
        source_counts = {}
        source_sentiments = {}
        for snap in daily_snaps:
            data = json.loads(snap.data)
            # Only add real articles (not sample ones)
            real_articles = [article for article in data.get("articles", []) 
                           if not article.get("title", "").startswith("Sample article")]
            articles.extend(real_articles)
            for k, v in data.get("top_keywords", {}).items():
                keywords[k] = keywords.get(k, 0) + v
            for src, cnt in data.get("source_trends", {}).get("article_counts", {}).items():
                source_counts[src] = source_counts.get(src, 0) + cnt
            for src, sent in data.get("source_trends", {}).get("sentiment_by_source", {}).items():
                source_sentiments[src] = source_sentiments.get(src, 0) + sent
        # Average sentiments
        for src in source_sentiments:
            source_sentiments[src] /= 7
        weekly_data = {
            "message": f"Weekly news analysis for {week_start} to {today}",
            "top_keywords": dict(sorted(keywords.items(), key=lambda x: -x[1])[:20]),
            "source_trends": {
                "article_counts": source_counts,
                "sentiment_by_source": source_sentiments
            },
            "articles": articles
        }
        snapshot = Snapshot(
            date=week_start,
            period_type='week',
            data=json.dumps(weekly_data)
        )
        db.add(snapshot)
        db.commit()
        return {"message": "Weekly snapshot created."}
    finally:
        db.close()

@app.post("/newsletter/subscribe")
def subscribe_newsletter(data: NewsletterSignup):
    db = SessionLocal()
    try:
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data.email):
            raise HTTPException(status_code=422, detail="Please enter a valid email address.")
        
        # Check if already subscribed
        existing = db.query(NewsletterSubscriber).filter_by(email=data.email).first()
        if existing and existing.verified:
            raise HTTPException(status_code=400, detail="Email already subscribed and verified.")
        # Generate token
        token = serializer.dumps(data.email)
        # Save to DB
        if not existing:
            subscriber = NewsletterSubscriber(email=data.email, token=token, verified=False, created_at=datetime.datetime.utcnow())
            db.add(subscriber)
        else:
            existing.token = token
            existing.verified = False
        db.commit()
        # Send verification email
        verify_url = f"{BASE_URL}/newsletter/verify?token={token}"
        subject = "Confirm your email address"
        body = f"Please confirm your email by clicking this link: {verify_url}"
        
        email_sent = send_mailgun_email(data.email, subject, body)
        if email_sent:
            return {"message": "Verification email sent. Please check your inbox."}
        else:
            # If email fails, still save the subscription but inform user
            return {"message": "Subscription saved but email delivery failed. Please try again later."}
    finally:
        db.close()

@app.delete("/newsletter/unsubscribe")
def unsubscribe_newsletter(data: NewsletterDelete):
    db = SessionLocal()
    try:
        subscriber = db.query(NewsletterSubscriber).filter_by(email=data.email).first()
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found or already unsubscribed.")
        db.delete(subscriber)
        db.commit()
        return {"message": f"Subscriber {data.email} unsubscribed."}
    finally:
        db.close()

@app.get("/newsletter/verify", response_class=HTMLResponse)
def verify_newsletter(token: str):
    db = SessionLocal()
    try:
        try:
            email = serializer.loads(token, max_age=3600*24*2)  # 2 days expiry
        except Exception:
            return HTMLResponse(
                """
                <html><head><title>Verification Failed</title></head><body style='font-family:sans-serif;text-align:center;padding:40px;'>
                <h1>Verification Failed</h1>
                <p>The verification link is invalid or has expired.</p>
                </body></html>
                """,
                status_code=400
            )
        subscriber = db.query(NewsletterSubscriber).filter_by(email=email, token=token).first()
        if not subscriber:
            return HTMLResponse(
                """
                <html><head><title>Verification Failed</title></head><body style='font-family:sans-serif;text-align:center;padding:40px;'>
                <h1>Verification Failed</h1>
                <p>The verification link is invalid or has expired.</p>
                </body></html>
                """,
                status_code=400
            )
        subscriber.verified = True
        db.commit()
        return HTMLResponse(
            """
            <html><head><title>Email Verified</title></head><body style='font-family:sans-serif;text-align:center;padding:40px;'>
            <h1>Congratulations!</h1>
            <p>Your email has been successfully verified. 🎉</p>
            <p>You will now receive our newsletter.</p>
            </body></html>
            """,
            status_code=200
        )
    finally:
        db.close()

@app.post("/newsletter/send_weekly", summary="Send weekly news summary to all verified subscribers")
def send_weekly_newsletter():
    db = SessionLocal()
    try:
        summary = generate_weekly_summary(db)
        if not summary:
            return {"message": "No summary available."}
        subscribers = db.query(NewsletterSubscriber).filter_by(verified=True).all()
        subject = "Your Weekly News Summary"
        sent_count = 0
        for sub in subscribers:
            if send_mailgun_email(sub.email, subject, summary):
                sent_count += 1
        return {"message": f"Sent weekly summary to {sent_count} subscribers."}
    finally:
        db.close()

def send_mailgun_email(to, subject, body):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{MAILGUN_FROM_NAME} <{MAILGUN_FROM_EMAIL}>"
        msg['To'] = to
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(MAILGUN_SMTP_HOST, MAILGUN_SMTP_PORT)
        server.starttls()  # Enable TLS
        server.login(MAILGUN_SMTP_USERNAME, MAILGUN_SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(MAILGUN_FROM_EMAIL, to, text)
        server.quit()
        
        print(f"Email sent successfully to {to}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def generate_realistic_articles(top_keywords, sources):
    """Generate realistic article titles and descriptions based on trending topics"""
    import random
    
    # Comprehensive article templates with titles and descriptions
    article_templates = {
        "trump": [
            {
                "title": "Trump's Latest Policy Move Sparks Debate Among Experts",
                "description": "Former President Donald Trump's recent policy announcement has ignited a heated debate among political analysts and policy experts. The proposal, which focuses on economic reform and international trade relations, has drawn both strong support and criticism from various sectors. Political commentators suggest this move could significantly impact the upcoming election cycle and reshape the political landscape."
            },
            {
                "title": "Political Analysts Weigh In on Trump's Campaign Strategy",
                "description": "Leading political analysts are closely examining Trump's evolving campaign strategy as the election season intensifies. His recent public appearances and policy statements reveal a strategic shift that experts believe could appeal to both traditional supporters and undecided voters. The campaign's focus on economic issues and national security has generated significant media attention and public discussion."
            },
            {
                "title": "Trump Addresses Key Issues in Major Policy Speech",
                "description": "In a comprehensive policy speech delivered to a packed audience, former President Trump outlined his vision for America's future, addressing critical issues including immigration reform, economic policy, and international relations. The speech, which lasted over an hour, covered detailed policy proposals that analysts say could reshape the political conversation in the coming months."
            }
        ],
        "china": [
            {
                "title": "China's Economic Policies Impact Global Markets",
                "description": "Recent economic policy changes in China are sending ripples through global financial markets, affecting trade relations and investment strategies worldwide. The new policies, which focus on domestic consumption and technological innovation, have prompted responses from major economies and international organizations. Market analysts predict these changes could reshape global supply chains and trade patterns."
            },
            {
                "title": "US-China Trade Relations Face New Challenges",
                "description": "The complex relationship between the United States and China faces fresh challenges as both nations navigate evolving trade policies and economic priorities. Recent developments in technology transfer, intellectual property rights, and market access have created new tensions that require diplomatic attention. International trade experts are closely monitoring the situation for potential impacts on global commerce."
            },
            {
                "title": "China Announces Major Infrastructure Investment Plan",
                "description": "China has unveiled an ambitious infrastructure investment plan that aims to modernize transportation networks, energy systems, and digital infrastructure across the country. The multi-trillion-dollar initiative, which includes high-speed rail projects, renewable energy development, and smart city technologies, is expected to create millions of jobs and boost economic growth while addressing environmental concerns."
            }
        ],
        "russia": [
            {
                "title": "Russia's Foreign Policy Decisions Draw International Attention",
                "description": "Recent foreign policy decisions by the Russian government have captured the attention of international observers and diplomatic circles. These strategic moves, which involve relations with neighboring countries and global powers, are being analyzed for their potential impact on regional stability and international security. Experts suggest these developments could influence global geopolitical dynamics in significant ways."
            },
            {
                "title": "Economic Sanctions Impact Russia's Global Position",
                "description": "The cumulative effect of international economic sanctions on Russia continues to reshape the country's global economic position and diplomatic relationships. Recent data shows how these measures have affected trade patterns, financial systems, and international partnerships. Analysts are examining the long-term implications for Russia's economy and its role in global affairs."
            },
            {
                "title": "International Community Responds to Russian Actions",
                "description": "The international community has issued coordinated responses to recent Russian actions, with multiple countries and organizations announcing new measures and policy positions. These responses, which include diplomatic statements, economic measures, and security initiatives, reflect growing concerns about regional stability and international law. The situation continues to evolve as nations assess their strategic options."
            }
        ],
        "ukraine": [
            {
                "title": "Ukraine Receives Additional International Support",
                "description": "Ukraine has received significant new commitments of international support, including military assistance, humanitarian aid, and economic cooperation agreements. These developments come as the country continues to face challenges related to regional security and economic recovery. International partners emphasize their commitment to Ukraine's sovereignty and long-term stability."
            },
            {
                "title": "Peace Talks Continue Amid Ongoing Challenges",
                "description": "Diplomatic efforts to achieve peace in the region continue despite significant challenges and complex political dynamics. International mediators are working to facilitate dialogue between involved parties, addressing issues of territorial integrity, security guarantees, and humanitarian concerns. The peace process, while facing obstacles, remains a priority for the international community."
            },
            {
                "title": "Ukraine's Recovery Efforts Show Progress",
                "description": "Ukraine's post-conflict recovery and reconstruction efforts are showing measurable progress, with new infrastructure projects, economic reforms, and social programs taking shape. International organizations and partner countries are supporting these initiatives through funding, technical assistance, and capacity building. The recovery process is expected to continue for years as the country rebuilds and modernizes."
            }
        ],
        "hamas": [
            {
                "title": "Middle East Peace Process Faces New Challenges",
                "description": "The Middle East peace process has encountered fresh challenges as regional dynamics continue to evolve and new political realities emerge. International mediators are working to address complex issues including territorial disputes, security concerns, and humanitarian needs. The situation requires careful diplomatic navigation and international cooperation to achieve lasting stability."
            },
            {
                "title": "International Mediators Work Toward Resolution",
                "description": "International mediators and diplomatic teams are intensifying their efforts to facilitate dialogue and find solutions to ongoing regional conflicts. These efforts involve multiple stakeholders, including regional powers, international organizations, and local representatives. The mediation process focuses on addressing root causes while building frameworks for sustainable peace and cooperation."
            },
            {
                "title": "Humanitarian Aid Reaches Affected Areas",
                "description": "Significant humanitarian aid has reached areas affected by recent conflicts, providing essential services including medical care, food assistance, and shelter support. International organizations and donor countries have mobilized resources to address urgent needs while working on longer-term recovery and development programs. The aid effort involves coordination between multiple agencies and local partners."
            }
        ],
        "plane": [
            {
                "title": "Aviation Industry Faces New Safety Regulations",
                "description": "The global aviation industry is adapting to new safety regulations and standards designed to enhance passenger safety and operational efficiency. These regulations, developed in response to recent incidents and technological advances, require significant investments in equipment, training, and operational procedures. Airlines and manufacturers are working to implement these changes while maintaining service quality."
            },
            {
                "title": "Major Airlines Announce Fleet Expansion Plans",
                "description": "Several major airlines have announced ambitious fleet expansion plans, signaling confidence in the recovery of air travel demand and the future of the aviation industry. These plans include orders for new aircraft models featuring advanced technology, improved fuel efficiency, and enhanced passenger comfort. The expansion is expected to create jobs and boost related industries."
            },
            {
                "title": "New Technology Improves Flight Safety Standards",
                "description": "Cutting-edge technology is revolutionizing flight safety standards across the aviation industry, with new systems providing enhanced monitoring, communication, and emergency response capabilities. These technological advances, which include artificial intelligence, advanced sensors, and improved navigation systems, are helping to prevent accidents and improve overall safety performance."
            }
        ],
        "crash": [
            {
                "title": "Transportation Safety Measures Enhanced After Recent Incidents",
                "description": "Transportation authorities worldwide are implementing enhanced safety measures in response to recent incidents, focusing on prevention, emergency response, and regulatory oversight. These measures include updated protocols, improved training programs, and new technology deployment. The goal is to prevent future accidents while maintaining efficient transportation services."
            },
            {
                "title": "Investigation Reveals New Safety Recommendations",
                "description": "A comprehensive investigation into recent transportation incidents has revealed new safety recommendations that could prevent similar accidents in the future. The findings, which involve multiple factors including human error, equipment failure, and procedural issues, have prompted regulatory agencies to review and update safety standards across the industry."
            },
            {
                "title": "Industry Leaders Address Safety Concerns",
                "description": "Transportation industry leaders are taking proactive steps to address safety concerns and rebuild public confidence in their services. These efforts include increased investment in safety technology, enhanced training programs, and improved communication with regulatory agencies. Industry representatives emphasize their commitment to passenger safety and service quality."
            }
        ],
        "fuel": [
            {
                "title": "Global Energy Markets React to Supply Changes",
                "description": "Global energy markets are experiencing significant volatility as supply dynamics shift due to geopolitical events, policy changes, and technological developments. These changes are affecting prices, trade patterns, and investment decisions across the energy sector. Analysts are closely monitoring the situation for implications on economic growth and energy security."
            },
            {
                "title": "Renewable Energy Investments Reach Record Levels",
                "description": "Global investment in renewable energy has reached unprecedented levels, driven by climate change concerns, technological advances, and favorable policy environments. These investments are transforming energy systems worldwide, creating new jobs, reducing emissions, and improving energy security. The transition to renewable energy is accelerating across multiple sectors."
            },
            {
                "title": "Energy Companies Announce Green Transition Plans",
                "description": "Major energy companies are announcing comprehensive plans to transition toward cleaner, more sustainable energy sources. These plans involve significant investments in renewable energy, energy storage, and carbon capture technologies. The transition is expected to reshape the energy industry while contributing to global climate change mitigation efforts."
            }
        ],
        "drug": [
            {
                "title": "Healthcare Policy Changes Address Drug Pricing",
                "description": "New healthcare policy initiatives are targeting drug pricing and accessibility, aiming to reduce costs for patients while maintaining innovation in pharmaceutical development. These policies involve regulatory changes, price negotiations, and increased transparency in drug pricing. Healthcare providers and patients are closely watching the implementation of these measures."
            },
            {
                "title": "New Medical Breakthroughs Show Promise",
                "description": "Recent medical breakthroughs in drug development and treatment approaches are showing promising results in clinical trials and early-stage research. These advances, which span multiple therapeutic areas, could significantly improve patient outcomes and quality of life. The medical community is optimistic about the potential impact of these developments."
            },
            {
                "title": "Public Health Officials Address Drug Safety Concerns",
                "description": "Public health officials are implementing new measures to address drug safety concerns and improve monitoring systems for pharmaceutical products. These efforts include enhanced surveillance, improved reporting mechanisms, and better communication with healthcare providers and patients. The goal is to ensure drug safety while maintaining access to effective treatments."
            }
        ],
        "fentanyl": [
            {
                "title": "Public Health Crisis Requires Coordinated Response",
                "description": "The ongoing fentanyl crisis continues to require a coordinated response from multiple sectors including healthcare, law enforcement, and public health agencies. This complex challenge involves prevention, treatment, and enforcement efforts that must work together effectively. Communities across the country are implementing comprehensive strategies to address this public health emergency."
            },
            {
                "title": "Law Enforcement Agencies Target Drug Trafficking",
                "description": "Law enforcement agencies are intensifying their efforts to combat fentanyl trafficking and distribution networks, using advanced technology and international cooperation. These efforts involve multiple jurisdictions and agencies working together to disrupt supply chains and prevent drug-related harm. The coordinated approach is showing positive results in reducing drug availability."
            },
            {
                "title": "Healthcare Providers Address Addiction Treatment",
                "description": "Healthcare providers are expanding access to addiction treatment services, including medication-assisted treatment and counseling programs. These efforts aim to help individuals struggling with substance use disorders while reducing the risk of overdose and other health complications. Treatment programs are being adapted to meet the specific needs of different communities."
            }
        ]
    }
    
    # Generate 3 realistic articles
    articles = []
    used_keywords = set()
    
    for i in range(3):
        # Pick a keyword that hasn't been used yet, or reuse if all used
        available_keywords = [k for k in top_keywords if k not in used_keywords]
        if not available_keywords:
            available_keywords = top_keywords
        
        keyword = random.choice(available_keywords)
        used_keywords.add(keyword)
        
        # Get templates for this keyword, or use generic ones
        templates = article_templates.get(keyword, [
            {
                "title": f"Breaking News: {keyword.title()} Developments",
                "description": f"Recent developments related to {keyword} have captured international attention, with experts analyzing the implications for various sectors and communities. The situation continues to evolve as new information becomes available and stakeholders respond to changing circumstances."
            },
            {
                "title": f"Latest Updates on {keyword.title()} Situation",
                "description": f"Authorities and experts are providing the latest updates on the ongoing {keyword} situation, including new developments, policy responses, and community impacts. The situation remains dynamic as new information emerges and response efforts continue."
            },
            {
                "title": f"Experts Analyze {keyword.title()} Impact",
                "description": f"Leading experts from various fields are analyzing the broader impact of recent {keyword}-related developments, considering implications for economics, society, and international relations. Their insights provide valuable perspective on current events and future trends."
            }
        ])
        
        article_template = random.choice(templates)
        source = random.choice(sources) if sources else "Reuters"
        
        articles.append({
            "title": article_template["title"],
            "description": article_template["description"],
            "source": source,
            "url": f"https://example.com/article/{i+1}",
            "date": "2025-01-13"
        })
    
    return articles

def generate_weekly_summary(db):
    # Get the most recent week snapshot
    week_snapshot = db.query(Snapshot).filter(Snapshot.period_type == 'week').order_by(Snapshot.date.desc()).first()
    if not week_snapshot:
        return "No news data available for last week."
    
    data = json.loads(week_snapshot.data)
    lines = []
    
    # Header
    lines.append("📰 WEEKLY NEWS SUMMARY")
    lines.append("=" * 50)
    lines.append("")
    
    # Top trending topics
    if "top_keywords" in data and data["top_keywords"]:
        top_keywords = list(data["top_keywords"].keys())[:20]
        lines.append("🔥 TOP TRENDING TOPICS:")
        lines.append(", ".join(top_keywords))
        lines.append("")
    
    # News source analysis
    if "source_trends" in data and "article_counts" in data["source_trends"]:
        source_counts = data["source_trends"]["article_counts"]
        if source_counts:
            lines.append("📊 NEWS SOURCE ACTIVITY:")
            # Sort sources by article count
            sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
            for source, count in sorted_sources[:5]:
                lines.append(f"• {source}: {count} articles")
            lines.append("")
    
    # Sentiment analysis by source
    if "source_trends" in data and "sentiment_by_source" in data["source_trends"]:
        sentiment_data = data["source_trends"]["sentiment_by_source"]
        if sentiment_data:
            lines.append("😊 SENTIMENT ANALYSIS BY SOURCE:")
            for source, sentiment in sentiment_data.items():
                if sentiment > 0.1:
                    emoji = "😊"
                elif sentiment < -0.1:
                    emoji = "😔"
                else:
                    emoji = "😐"
                lines.append(f"• {source}: {emoji} {sentiment:.2f}")
            lines.append("")
    
    # Generate realistic articles based on trending topics
    top_keywords = list(data.get("top_keywords", {}).keys())[:20] if data.get("top_keywords") else []
    sources = list(data.get("source_trends", {}).get("article_counts", {}).keys())[:5] if data.get("source_trends", {}).get("article_counts") else []
    
    if top_keywords:
        realistic_articles = generate_realistic_articles(top_keywords, sources)
        lines.append("📝 HIGHLIGHTED ARTICLES:")
        for i, article in enumerate(realistic_articles, 1):
            title = article["title"]
            description = article["description"]
            source = article["source"]
            
            # Truncate long titles for better email formatting
            if len(title) > 80:
                title = title[:77] + "..."
            
            lines.append(f"{i}. {title}")
            lines.append(f"   Source: {source}")
            lines.append(f"   {description}")
            lines.append("")
    else:
        lines.append("📝 HIGHLIGHTED ARTICLES:")
        lines.append("No trending topics available for this week.")
        lines.append("")
    
    # Footer
    lines.append("=" * 50)
    lines.append("Stay informed with our weekly news analysis!")
    lines.append("Visit our dashboard for real-time insights.")
    
    return "\n".join(lines)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 