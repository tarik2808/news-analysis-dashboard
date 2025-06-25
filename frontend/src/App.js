import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';
import { Route, Routes, useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import './App.css';
import LearnMore from './LearnMore';

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

function App() {
  // State management
  const [activeFAQ, setActiveFAQ] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newsData, setNewsData] = useState(() => {
    const stored = localStorage.getItem('newsData');
    return stored ? JSON.parse(stored) : null;
  });
  const [trendsData, setTrendsData] = useState(() => {
    const stored = localStorage.getItem('trendsData');
    return stored ? JSON.parse(stored) : null;
  });
  const [showCharts, setShowCharts] = useState(() => {
    const stored = localStorage.getItem('showCharts');
    return stored ? JSON.parse(stored) : false;
  });
  const [scrapingStatus, setScrapingStatus] = useState('');
  const navigate = useNavigate();
  const chartsRef = useRef(null);
  const topRef = useRef(null);
  const sentimentRef = useRef(null);
  const trendingRef = useRef(null);

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('newsData', JSON.stringify(newsData));
  }, [newsData]);
  useEffect(() => {
    localStorage.setItem('trendsData', JSON.stringify(trendsData));
  }, [trendsData]);
  useEffect(() => {
    localStorage.setItem('showCharts', JSON.stringify(showCharts));
  }, [showCharts]);

  // FAQ toggle functionality
  const toggleFAQ = (index) => {
    setActiveFAQ(activeFAQ === index ? null : index);
  };

  // Backend API calls
  const runFullPipeline = async () => {
    setLoading(true);
    setError(null);
    setScrapingStatus('Running full analysis pipeline...');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/full_pipeline`, {
        articles_per_source: 10
      });
      
      // Set the data from the full pipeline response
      setNewsData({
        message: response.data.message,
        articles: response.data.articles || []
      });
      setTrendsData({
        top_keywords: response.data.top_keywords,
        source_trends: response.data.source_trends,
        temporal_trends: response.data.temporal_trends
      });
      setShowCharts(true);
      setScrapingStatus(`Pipeline completed! ${response.data.message}`);
      
    } catch (err) {
      setError('Failed to run analysis pipeline. Please try again.');
      setScrapingStatus('Pipeline failed.');
      console.error('Pipeline error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Legacy functions (keeping for backward compatibility)
  const scrapeNews = async () => {
    // Redirect to the new full pipeline
    await runFullPipeline();
  };

  const analyzeTrends = async (articles) => {
    // This function is now handled by the full pipeline
    console.log('Trend analysis is now part of the full pipeline');
  };

  // Chart data preparation
  const prepareSentimentData = () => {
    if (!newsData?.articles) return [];
    
    const sentimentCounts = {
      positive: 0,
      negative: 0,
      neutral: 0
    };

    newsData.articles.forEach(article => {
      const polarity = article.sentiment_polarity || 0;
      if (polarity > 0.1) sentimentCounts.positive++;
      else if (polarity < -0.1) sentimentCounts.negative++;
      else sentimentCounts.neutral++;
    });

    return [
      { name: 'Positive', value: sentimentCounts.positive, color: '#10b981' },
      { name: 'Negative', value: sentimentCounts.negative, color: '#ef4444' },
      { name: 'Neutral', value: sentimentCounts.neutral, color: '#6b7280' }
    ];
  };

  const prepareSourceData = () => {
    if (!newsData?.articles) return [];
    
    const sourceCounts = {};
    newsData.articles.forEach(article => {
      const source = article.source || 'Unknown';
      sourceCounts[source] = (sourceCounts[source] || 0) + 1;
    });

    return Object.entries(sourceCounts).map(([source, count]) => ({
      source,
      count
    }));
  };

  const prepareTrendingKeywords = () => {
    if (!trendsData?.top_keywords) {
      console.log('[DEBUG] No trendsData or top_keywords found:', trendsData);
      return [];
    }
    
    const keywordData = Object.entries(trendsData.top_keywords)
      .slice(0, 10)
      .map(([keyword, count]) => ({
        keyword,
        count
      }));
    
    console.log('[DEBUG] Prepared keyword data:', keywordData);
    console.log('[DEBUG] Raw top_keywords:', trendsData.top_keywords);
    
    return keywordData;
  };

  return (
    <Routes>
      <Route path="/" element={
        <div className="dashboard-root">
          <div ref={topRef}></div>
          {/* Hero Section */}
          <section className="hero-section">
            <img src={process.env.PUBLIC_URL + '/dashboardhero.png'} alt="Dashboard Hero" className="hero-image" />
            <div className="hero-content">
              <h1>Spot trends. Analyze news. Instantly.</h1>
              <p>Welcome to your all-in-one news analysis dashboard. Dive into real-time insights, track emerging stories, and visualize trends from top sources. Whether you're a data enthusiast, journalist, or researcher, discover smarter ways to explore the news—together.</p>
              <div className="hero-buttons">
                <button 
                  className="primary-btn" 
                  onClick={runFullPipeline}
                  disabled={loading}
                >
                  {loading ? 'Running Analysis...' : 'Run Full Analysis'}
                </button>
                <button className="secondary-btn" onClick={() => navigate('/learn-more')}>Learn More</button>
              </div>
              {scrapingStatus && (
                <div className="status-message">
                  {scrapingStatus}
                </div>
              )}
            </div>
          </section>

          {/* Feature Cards */}
          <section className="features-section">
            <div className="features-container">
              <div className="feature-card">
                <img src={process.env.PUBLIC_URL + '/icon_article_count.png'} alt="Article Count" className="feature-icon" />
                <h3>Article Count</h3>
                <p>Track the volume of news coverage across different sources and topics.</p>
                <div className="feature-stat">
                  {newsData ? newsData.articles.length : '0'} Articles
                </div>
              </div>
              
              <div className="feature-card">
                <img src={process.env.PUBLIC_URL + '/icon_sentiment.png'} alt="Sentiment Analysis" className="feature-icon" />
                <h3>Sentiment Insights</h3>
                <p>Understand the emotional tone and sentiment of news coverage.</p>
                <div className="feature-stat">
                  {newsData ? 'Real-time' : 'Ready'}
                </div>
              </div>
              
              <div className="feature-card">
                <img src={process.env.PUBLIC_URL + '/icon_trending.png'} alt="Trending Topics" className="feature-icon" />
                <h3>Trending Topics</h3>
                <p>Discover emerging stories and trending keywords in real-time.</p>
                <div className="feature-stat">
                  {trendsData ? Object.keys(trendsData.top_keywords || {}).length : '0'} Trends
                </div>
              </div>
            </div>
          </section>

          {/* Error Display */}
          {error && (
            <div className="error-message">
              <p>{error}</p>
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          )}

          {/* Data Visualization Section */}
          {showCharts && newsData && (
            <section className="charts-section" ref={chartsRef}>
              <div className="charts-container">
                <h2>News Analysis Dashboard</h2>
                
                <div className="charts-grid">
                  {/* Sentiment Distribution */}
                  <div className="chart-card">
                    <h3>Sentiment Distribution</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={prepareSentimentData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {prepareSentimentData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Source Distribution */}
                  <div className="chart-card">
                    <h3>Articles by Source</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={prepareSourceData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="source" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="count" fill="#2563eb" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Trending Keywords */}
                  <div className="chart-card full-width">
                    <h3>Top Trending Keywords</h3>
                    {(() => {
                      // Sort by count descending before slicing top 10
                      const keywordData = Object.entries(trendsData?.top_keywords || {})
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 10)
                        .map(([keyword, count]) => ({ keyword, count }));
                      const chartHeight = Math.max(300, keywordData.length * 40);
                      console.log('[DEBUG] Chart data for trending keywords:', keywordData);
                      return (
                        <ResponsiveContainer width="100%" height={chartHeight}>
                          <BarChart data={keywordData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" />
                            <YAxis dataKey="keyword" type="category" width={100} />
                            <Tooltip />
                            <Bar dataKey="count" fill="#10b981" />
                          </BarChart>
                        </ResponsiveContainer>
                      );
                    })()}
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Sentiment Analysis Section */}
          <section className="sentiment-section" id="sentiment-section" ref={sentimentRef}>
            <div className="sentiment-container">
              <img src={process.env.PUBLIC_URL + '/sentiment.png'} alt="Sentiment Analysis" className="sentiment-image" />
              <div className="sentiment-content">
                <h2>See sentiment at a glance</h2>
                <p>Curious about the mood in today's headlines? Instantly spot positive, negative, or neutral coverage with easy-to-read charts and clear breakdowns.</p>
                <button 
                  className="primary-btn"
                  onClick={() => setShowCharts(!showCharts)}
                >
                  {showCharts ? 'Hide Charts' : 'View Charts'}
                </button>
              </div>
            </div>
          </section>

          {/* Real-time News Stats Section */}
          <section className="stats-section">
            <div className="stats-container">
              <img src={process.env.PUBLIC_URL + '/realtimesnews.png'} alt="Real-time News Stats" className="stats-image" />
              <div className="stats-content">
                <h2>Real-time news, real insights</h2>
                <p>Get a live snapshot of the news landscape. See article counts, sources, and sentiment as they update—so you're always in the know, right when it matters.</p>
                <button 
                  className="primary-btn"
                  onClick={runFullPipeline}
                  disabled={loading}
                >
                  {loading ? 'Updating...' : 'Refresh Data'}
                </button>
              </div>
            </div>
          </section>

          {/* Trending Topics Section */}
          <section className="trending-section" id="trending-section" ref={trendingRef}>
            <div className="trending-container">
              <img src={process.env.PUBLIC_URL + '/trend.png'} alt="Trending Topics" className="trending-image" />
              <div className="trending-content">
                <h2>Discover what's trending</h2>
                <p>Stay ahead of the curve with our trending topics analysis. See which stories are gaining momentum and explore the conversations that matter most.</p>
                <button 
                  className="primary-btn"
                  onClick={() => {
                    setShowCharts(true);
                    setTimeout(() => {
                      chartsRef.current?.scrollIntoView({ behavior: 'smooth' });
                    }, 100);
                  }}
                >
                  Explore Trends
                </button>
              </div>
            </div>
          </section>

          {/* FAQ Section */}
          <section className="faq-section">
            <div className="faq-container">
              <h2>Frequently Asked Questions</h2>
              <div className="faq-list">
                <div className={`faq-item ${activeFAQ === 0 ? 'active' : ''}`}>
                  <div className="faq-question" onClick={() => toggleFAQ(0)}>
                    <h3>How often is the data updated?</h3>
                    <span className="faq-toggle">+</span>
                  </div>
                  <div className="faq-answer">
                    <p>Our news analysis platform updates data in real-time as new articles are published from our monitored sources (BBC, CNN, Reuters). You'll see fresh insights and trends as they emerge.</p>
                  </div>
                </div>
                
                <div className={`faq-item ${activeFAQ === 1 ? 'active' : ''}`}>
                  <div className="faq-question" onClick={() => toggleFAQ(1)}>
                    <h3>What sources do you analyze?</h3>
                    <span className="faq-toggle">+</span>
                  </div>
                  <div className="faq-answer">
                    <p>We currently analyze articles from BBC, CNN, and Reuters. These major international news sources provide comprehensive coverage across politics, business, technology, and global events.</p>
                  </div>
                </div>
                
                <div className={`faq-item ${activeFAQ === 2 ? 'active' : ''}`}>
                  <div className="faq-question" onClick={() => toggleFAQ(2)}>
                    <h3>How accurate is the sentiment analysis?</h3>
                    <span className="faq-toggle">+</span>
                  </div>
                  <div className="faq-answer">
                    <p>Our sentiment analysis uses advanced NLP techniques to classify articles as positive, negative, or neutral. While highly accurate, it's designed to provide insights rather than definitive judgments.</p>
                  </div>
                </div>
                
                <div className={`faq-item ${activeFAQ === 3 ? 'active' : ''}`}>
                  <div className="faq-question" onClick={() => toggleFAQ(3)}>
                    <h3>Can I export the data?</h3>
                    <span className="faq-toggle">+</span>
                  </div>
                  <div className="faq-answer">
                    <p>Yes! You can export analyzed data in CSV format, including article details, sentiment scores, and trend analysis. Perfect for further research or reporting.</p>
                  </div>
                </div>
                
                <div className={`faq-item ${activeFAQ === 4 ? 'active' : ''}`}>
                  <div className="faq-question" onClick={() => toggleFAQ(4)}>
                    <h3>Is this free to use?</h3>
                    <span className="faq-toggle">+</span>
                  </div>
                  <div className="faq-answer">
                    <p>Currently, our news analysis platform is available for free. We're committed to making data-driven insights accessible to researchers, journalists, and news enthusiasts.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="dashboard-footer">
            <div className="footer-container">
              <div className="footer-content">
                <div className="footer-section">
                  <h3>News Analysis Platform</h3>
                  <p>Your all-in-one solution for real-time news insights, sentiment analysis, and trend discovery from top international sources.</p>
                </div>
                <div className="footer-section">
                  <h4>Quick Links</h4>
                  <ul>
                    <li><button style={{background:'none',border:'none',color:'#cbd5e1',cursor:'pointer',padding:0}} onClick={() => {
                      if (window.location.pathname === '/') {
                        topRef.current?.scrollIntoView({ behavior: 'smooth' });
                      } else {
                        navigate('/');
                        setTimeout(() => {
                          topRef.current?.scrollIntoView({ behavior: 'smooth' });
                        }, 100);
                      }
                    }}>Dashboard</button></li>
                    <li><button style={{background:'none',border:'none',color:'#cbd5e1',cursor:'pointer',padding:0}} onClick={() => {
                      if (window.location.pathname === '/') {
                        sentimentRef.current?.scrollIntoView({ behavior: 'smooth' });
                      } else {
                        navigate('/');
                        setTimeout(() => {
                          sentimentRef.current?.scrollIntoView({ behavior: 'smooth' });
                        }, 100);
                      }
                    }}>Sentiment Analysis</button></li>
                    <li><button style={{background:'none',border:'none',color:'#cbd5e1',cursor:'pointer',padding:0}} onClick={() => {
                      if (window.location.pathname === '/') {
                        trendingRef.current?.scrollIntoView({ behavior: 'smooth' });
                      } else {
                        navigate('/');
                        setTimeout(() => {
                          trendingRef.current?.scrollIntoView({ behavior: 'smooth' });
                        }, 100);
                      }
                    }}>Trending Topics</button></li>
                    <li><a href="#faq">FAQ</a></li>
                  </ul>
                </div>
                <div className="footer-section">
                  <h4>Contact</h4>
                  <ul>
                    <li><a href="mailto:tarik.coralic@stu.ibu.edu.ba">tarik.coralic@stu.ibu.edu.ba</a></li>
                    <li><a href="https://github.com/tarik2808/news-analysis-dashboard" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                    <li><a href="https://linkedin.com/in/yourusername" target="_blank" rel="noopener noreferrer">LinkedIn</a></li>
                  </ul>
                </div>
              </div>
              <div className="footer-bottom">
                <p>&copy; 2024 News Analysis Platform. Built with React and FastAPI.</p>
              </div>
            </div>
          </footer>
        </div>
      } />
      <Route path="/learn-more" element={<LearnMore />} />
    </Routes>
  );
}

export default App;
