# 📰 News Analysis Platform

A comprehensive news analysis platform that scrapes, processes, and analyzes news articles from top international sources (BBC, CNN, Reuters) with real-time sentiment analysis, trend detection, and interactive data visualization.

## 🚀 Features

### Backend (FastAPI)
- **News Scraping**: Automated scraping from BBC, CNN, and Reuters
- **Text Processing**: Advanced NLP text cleaning and preprocessing
- **Sentiment Analysis**: Real-time sentiment classification using TextBlob and spaCy
- **Trend Analysis**: Keyword extraction and trending topic detection
- **Data Visualization**: Automated chart generation and data export
- **RESTful API**: Complete API endpoints for all functionality

### Frontend (React)
- **Modern Dashboard**: Clean, responsive design with AI-generated visuals
- **Interactive Charts**: Real-time data visualization using Recharts
- **Live Updates**: Real-time news scraping and analysis
- **Responsive Design**: Mobile-friendly interface
- **Interactive FAQ**: Expandable questions and answers
- **Error Handling**: Comprehensive error states and loading indicators

## 🛠️ Tech Stack

### Backend
- **Python 3.8+**
- **FastAPI** - Modern web framework
- **BeautifulSoup4** - Web scraping
- **TextBlob** - Sentiment analysis
- **spaCy** - Advanced NLP (optional)
- **Pandas** - Data manipulation
- **Matplotlib/Seaborn** - Data visualization

### Frontend
- **React 18** - UI framework
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **CSS3** - Styling and animations

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd news-analysis-platform
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional: Install spaCy model for advanced NLP**
   ```bash
   python -m spacy download en_core_web_sm
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

## 🚀 Quick Start

### Option 1: Start Both Servers (Recommended)

python start_app.py

This will start both the backend (port 8000) and frontend (port 3000) automatically.

### Option 2: Start Servers Separately

**Backend:**

uvicorn api:app --host 0.0.0.0 --port 8000 --reload

**Frontend:**

cd frontend
npm start

## 🔧 Environment Variables

For the newsletter feature to work, you need to set up Mailgun SMTP credentials as environment variables:

### Windows (Command Prompt):
```cmd
set MAILGUN_SMTP_HOST=smtp.eu.mailgun.org
set MAILGUN_SMTP_PORT=587
set MAILGUN_SMTP_USERNAME=postmaster@mg.yourdomain.com
set MAILGUN_SMTP_PASSWORD=your_smtp_password_here
set MAILGUN_FROM_EMAIL=postmaster@mg.yourdomain.com
set MAILGUN_FROM_NAME=Your Project Name
```

### Windows (PowerShell):
```powershell
$env:MAILGUN_SMTP_HOST="smtp.eu.mailgun.org"
$env:MAILGUN_SMTP_PORT="587"
$env:MAILGUN_SMTP_USERNAME="postmaster@mg.yourdomain.com"
$env:MAILGUN_SMTP_PASSWORD="your_smtp_password_here"
$env:MAILGUN_FROM_EMAIL="postmaster@mg.yourdomain.com"
$env:MAILGUN_FROM_NAME="Your Project Name"
```

### Linux/Mac:
```bash
export MAILGUN_SMTP_HOST=smtp.eu.mailgun.org
export MAILGUN_SMTP_PORT=587
export MAILGUN_SMTP_USERNAME=postmaster@mg.yourdomain.com
export MAILGUN_SMTP_PASSWORD=your_smtp_password_here
export MAILGUN_FROM_EMAIL=postmaster@mg.yourdomain.com
export MAILGUN_FROM_NAME=Your Project Name
```

**Note:** Replace `your_smtp_password_here` with your actual Mailgun SMTP password and `mg.yourdomain.com` with your actual Mailgun domain.

## 🌐 Access Points

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API Docs**: http://localhost:8000/redoc

## 📊 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scrape` | POST | Scrape news articles from all sources |
| `/process` | POST | Process and clean text data |
| `/analyze` | POST | Analyze texts for sentiment and keywords |
| `/trends` | POST | Analyze trends from article data |
| `/download/{filename}` | GET | Download result files (CSV/plots) |

### Example API Usage

```python
import requests

# Scrape news articles
response = requests.post("http://localhost:8000/scrape", json={
    "articles_per_source": 10
})

# Analyze trends
trends_response = requests.post("http://localhost:8000/trends", json={
    "source": ["BBC", "CNN"],
    "title": ["Article 1", "Article 2"],
    "text": ["Content 1", "Content 2"],
    "url": ["url1", "url2"],
    "date": ["2024-01-01", "2024-01-01"]
})
```

## 🎯 Frontend Features

### Dashboard Sections

1. **Hero Section**
   - Eye-catching landing with call-to-action
   - Real-time scraping status
   - Start analysis button

2. **Feature Cards**
   - Article count with live updates
   - Sentiment insights status
   - Trending topics counter

3. **Interactive Charts**
   - Sentiment distribution pie chart
   - Articles by source bar chart
   - Top trending keywords horizontal bar chart

4. **Content Sections**
   - Sentiment analysis showcase
   - Real-time news stats
   - Trending topics exploration

5. **FAQ Section**
   - Expandable questions and answers
   - Smooth animations
   - Comprehensive platform information

### Interactive Features

- **Real-time Data**: Live updates from news scraping
- **Chart Toggle**: Show/hide data visualizations
- **Error Handling**: User-friendly error messages
- **Loading States**: Visual feedback during operations
- **Responsive Design**: Works on all device sizes

## 📈 Data Flow

1. **Scraping**: Frontend triggers news scraping via API
2. **Processing**: Backend processes and cleans article text
3. **Analysis**: Sentiment analysis and keyword extraction
4. **Trends**: Trend analysis and visualization
5. **Display**: Frontend renders interactive charts and stats

## 🎨 Design Features

- **Modern UI**: Clean, professional design inspired by modern dashboards
- **AI-Generated Images**: Custom visuals for each section
- **Color Scheme**: Professional blues, grays, and whites
- **Animations**: Smooth transitions and hover effects
- **Typography**: Clear, readable fonts with proper hierarchy

## 🔧 Configuration

### Backend Configuration

Edit `api.py` to modify:
- Scraping sources and limits
- Analysis parameters
- Output file locations

### Frontend Configuration

Edit `frontend/src/App.js` to modify:
- API endpoint URLs
- Chart configurations
- UI text and content

## 📁 Project Structure

```
news-analysis-platform/
├── api.py                 # FastAPI backend
├── main.py               # Main analysis pipeline
├── news_scraper.py       # Web scraping module
├── text_processor.py     # Text processing
├── nlp_analyzer.py       # Advanced NLP analysis
├── nlp_analyzer_simple.py # Simple NLP analysis
├── trend_analyzer.py     # Trend analysis
├── requirements.txt      # Python dependencies
├── start_app.py         # Combined startup script
├── frontend/            # React frontend
│   ├── src/
│   │   ├── App.js       # Main React component
│   │   ├── App.css      # Styles
│   │   └── index.js     # React entry point
│   ├── public/          # Static assets
│   └── package.json     # Node.js dependencies
├── ai_images/           # AI-generated visuals
├── trend_plots/         # Generated charts
├── data/               # Data files
└── logs/               # Application logs
```

## 🚀 Deployment

### Backend Deployment
- Deploy to cloud platforms (Heroku, AWS, Google Cloud)
- Use Docker for containerization
- Set up environment variables for configuration

### Frontend Deployment
- Build for production: `npm run build`
- Deploy to Netlify, Vercel, or similar platforms
- Configure API endpoint URLs for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the FAQ section in the application
- Review the API documentation at `/docs`
- Open an issue on GitHub

## 🎉 Acknowledgments

- News sources: BBC, CNN, Reuters
- Open-source libraries and frameworks
- AI image generation tools
- Community contributors

---

**Built with ❤️ for news analysis and data visualization** 