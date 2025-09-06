import axios from 'axios';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Route, Routes, useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import './App.css';
import LearnMore from './LearnMore';
import NewsletterSignup from './NewsletterSignup';

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

function App() {
  // State management
  const [activeFAQ, setActiveFAQ] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingStep, setLoadingStep] = useState('');
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
  const [donationAmount, setDonationAmount] = useState('');
  const [donationStatus, setDonationStatus] = useState('');
  const [donationLoading, setDonationLoading] = useState(false);
  const [articlesPerSource, setArticlesPerSource] = useState(10);
  const navigate = useNavigate();
  const chartsRef = useRef(null);
  const topRef = useRef(null);
  const sentimentRef = useRef(null);
  const trendingRef = useRef(null);
  const donationRef = useRef(null);
  const sepoliaAddress = '0x7a4E9CC12FA0F11e89E9cE164707947F97d2E0F5';
  const [timeRange, setTimeRange] = useState('today');

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
    setLoadingProgress(0);
    setLoadingStep('');
    setError(null);
    setScrapingStatus(`Running full analysis pipeline (${articlesPerSource} articles per source)...`);
    
    try {
      // Use the streaming endpoint for real-time progress
      const response = await fetch(`${API_BASE_URL}/full_pipeline_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          articles_per_source: articlesPerSource
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let result = null;
      let allArticles = [];
      let metadata = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim();
              if (!jsonStr) continue; // Skip empty lines
              
              const data = JSON.parse(jsonStr);
              
              if (data.status === 'running') {
                setLoadingStep(data.step);
                setLoadingProgress(data.progress);
                setScrapingStatus(data.step);
                
                // Handle metadata
                if (data.metadata) {
                  metadata = data.metadata;
                }
                
                // Handle article chunks
                if (data.articles_chunk) {
                  allArticles = allArticles.concat(data.articles_chunk);
                  console.log(`Received ${allArticles.length} articles so far...`);
                }
                
              } else if (data.status === 'completed') {
                result = data.result;
                setLoadingStep('Pipeline completed!');
                setLoadingProgress(100);
                setScrapingStatus(`Pipeline completed! ${result.message}`);
              } else if (data.status === 'error') {
                throw new Error(data.error || 'Pipeline failed');
              }
            } catch (parseError) {
              console.warn('Failed to parse progress data:', parseError);
              console.warn('Problematic line length:', line.length);
              console.warn('Line preview:', line.slice(0, 100) + '...');
              
              // If it's a JSON parsing error, it might be due to timestamp issues
              // or truncated data. Try to continue with the pipeline
              if (parseError.message.includes('Timestamp')) {
                console.warn('Timestamp serialization issue detected, continuing...');
              } else if (parseError.message.includes('Unterminated string')) {
                console.warn('JSON truncation detected, this might be due to large data payload');
              }
            }
          }
        }
      }

      if (result) {
        // Set the data from the completed pipeline
        setNewsData({
            message: result.message,
            articles: result.articles || []
        });
        setTrendsData({
            top_keywords: result.top_keywords,
            source_trends: result.source_trends,
            temporal_trends: result.temporal_trends
        });
        setShowCharts(true);
      } else if (metadata && allArticles.length > 0) {
        // Use chunked data if available
        console.log(`Using chunked data: ${allArticles.length} articles`);
        setNewsData({
            message: metadata.message,
            articles: allArticles
        });
        setTrendsData({
            top_keywords: metadata.top_keywords,
            source_trends: metadata.source_trends,
            temporal_trends: metadata.temporal_trends
        });
        setShowCharts(true);
      } else {
        throw new Error('No result received from pipeline');
      }
      
    } catch (err) {
      setError('Failed to run analysis pipeline. Please try again.');
      setScrapingStatus('Pipeline failed.');
      console.error('Pipeline error:', err);
    } finally {
      setLoading(false);
      setLoadingProgress(0);
      setLoadingStep('');
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

  const prepareSentimentBySourceData = () => {
    if (!newsData?.articles) return [];
    const sourceSentiments = {};
    const sourceCounts = {};

    newsData.articles.forEach(article => {
      const source = article.source || 'Unknown';
      const polarity = article.sentiment_polarity || 0;
      sourceSentiments[source] = (sourceSentiments[source] || 0) + polarity;
      sourceCounts[source] = (sourceCounts[source] || 0) + 1;
    });

    return Object.keys(sourceSentiments).map(source => ({
      source,
      avgSentiment: sourceCounts[source] ? sourceSentiments[source] / sourceCounts[source] : 0
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

  const prepareKeywordSentimentData = () => {
    if (!newsData?.articles || !trendsData?.top_keywords) {
      return [];
    }
    
    // Get top keywords
    const topKeywords = Object.keys(trendsData.top_keywords).slice(0, 15);
    
    // Calculate sentiment for each keyword
    const keywordSentimentData = topKeywords.map(keyword => {
      let totalSentiment = 0;
      let articleCount = 0;
      
      // Find articles that contain this keyword
      newsData.articles.forEach(article => {
        const text = (article.text || '').toLowerCase();
        const title = (article.title || '').toLowerCase();
        const keywordLower = keyword.toLowerCase();
        
        if (text.includes(keywordLower) || title.includes(keywordLower)) {
          totalSentiment += article.sentiment_polarity || 0;
          articleCount += 1;
        }
      });
      
      const avgSentiment = articleCount > 0 ? totalSentiment / articleCount : 0;
      const frequency = trendsData.top_keywords[keyword];
      
      return {
        keyword,
        frequency,
        sentiment: avgSentiment,
        articleCount
      };
    }).filter(item => item.articleCount > 0); // Only include keywords that appear in articles
    
    return keywordSentimentData;
  };

  const prepareTemporalTrendsData = () => {
    if (!newsData?.articles) {
      return [];
    }
    
    // Group articles by hour of the day
    const hourlyData = {};
    
    newsData.articles.forEach(article => {
      try {
        const articleDate = new Date(article.date);
        const hour = articleDate.getHours();
        const hourKey = `${hour.toString().padStart(2, '0')}:00`;
        
        if (!hourlyData[hourKey]) {
          hourlyData[hourKey] = {
            time: hourKey,
            hour: hour,
            articles: 0,
            totalSentiment: 0,
            avgSentiment: 0,
            positive: 0,
            negative: 0,
            neutral: 0
          };
        }
        
        const sentiment = article.sentiment_polarity || 0;
        hourlyData[hourKey].articles += 1;
        hourlyData[hourKey].totalSentiment += sentiment;
        
        // Categorize sentiment
        if (sentiment > 0.1) {
          hourlyData[hourKey].positive += 1;
        } else if (sentiment < -0.1) {
          hourlyData[hourKey].negative += 1;
        } else {
          hourlyData[hourKey].neutral += 1;
        }
      } catch (error) {
        console.warn('Error parsing date:', article.date, error);
      }
    });
    
    // Calculate average sentiment and convert to array
    const temporalData = Object.values(hourlyData)
      .map(data => ({
        ...data,
        avgSentiment: data.articles > 0 ? data.totalSentiment / data.articles : 0
      }))
      .sort((a, b) => a.hour - b.hour);
    
    return temporalData;
  };

  // MetaMask donation handler
  const handleDonate = useCallback(async () => {
    setDonationStatus('');
    if (!window.ethereum) {
      setDonationStatus('MetaMask is not installed.');
      return;
    }
    if (!donationAmount || isNaN(donationAmount) || Number(donationAmount) <= 0) {
      setDonationStatus('Please enter a valid amount.');
      return;
    }
    setDonationLoading(true);
    try {
      // Request account access if needed
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      const accounts = await window.ethereum.request({ method: 'eth_accounts' });
      const from = accounts[0];
      // Convert ETH to Wei
      const value = parseInt((Number(donationAmount) * 1e18).toString(), 10).toString(16);
      // Send transaction
      await window.ethereum.request({
        method: 'eth_sendTransaction',
        params: [{
          from,
          to: sepoliaAddress,
          value: '0x' + value,
          chainId: '0xaa36a7' // Sepolia chainId in hex
        }]
      });
      setDonationStatus('Thank you for your donation!');
      setDonationAmount('');
    } catch (err) {
      setDonationStatus('Transaction failed or cancelled.');
    }
    setDonationLoading(false);
  }, [donationAmount]);

  // Helper function to get ISO week number
  const getISOWeek = (date) => {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    // Thursday in current week decides the year
    d.setDate(d.getDate() + 3 - (d.getDay() + 6) % 7);
    // January 4 is always in week 1
    const week1 = new Date(d.getFullYear(), 0, 4);
    // Adjust to Thursday in week 1 and count number of weeks from date to week1
    const week = 1 + Math.round(((d.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
    return week;
  };

  // Fetch snapshot based on time range
  const fetchSnapshot = useCallback(async (range) => {
    setLoading(true);
    setError(null);
    
    // Clear localStorage cache to ensure fresh data
    localStorage.removeItem('newsData');
    localStorage.removeItem('trendsData');
    localStorage.removeItem('showCharts');
    
    let url = '';
    const today = new Date();
    
    if (range === 'today') {
      const year = today.getFullYear();
      const month = (today.getMonth() + 1).toString().padStart(2, '0');
      const day = today.getDate().toString().padStart(2, '0');
      url = `${API_BASE_URL}/snapshots/day/${year}-${month}-${day}`;
    } else if (range === 'week') {
      // Use rolling 7-day period instead of ISO week
      const year = today.getFullYear();
      const month = (today.getMonth() + 1).toString().padStart(2, '0');
      const day = today.getDate().toString().padStart(2, '0');
      url = `${API_BASE_URL}/snapshots/rolling-week/${year}-${month}-${day}`;
    } else if (range === 'month') {
      // Use rolling 30-day period instead of calendar month
      const year = today.getFullYear();
      const month = (today.getMonth() + 1).toString().padStart(2, '0');
      const day = today.getDate().toString().padStart(2, '0');
      url = `${API_BASE_URL}/snapshots/rolling-month/${year}-${month}-${day}`;
    }
    try {
      const response = await axios.get(url, { timeout: 10000 }); // 10s timeout
      setNewsData({ message: response.data.message, articles: response.data.articles || [] });
      setTrendsData({
        top_keywords: response.data.top_keywords,
        source_trends: response.data.source_trends,
        temporal_trends: response.data.temporal_trends
      });
      setShowCharts(true);
      setError(null);
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('The request timed out. Please try again later.');
      } else if (err.response && err.response.status === 404) {
        setError('No data available for this period. Please run the analysis on more days to see historical trends.');
      } else {
        setError('An error occurred while fetching data.');
      }
      setShowCharts(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch snapshot when timeRange changes
  useEffect(() => {
    fetchSnapshot(timeRange);
  }, [timeRange]);

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
              {/* Article Count Selector */}
              <div className="article-selector">
                <label htmlFor="articlesPerSource" className="selector-label">
                  Articles per source:
                </label>
                <div className="selector-container">
                  <input
                    type="range"
                    id="articlesPerSource"
                    min="5"
                    max="30"
                    value={articlesPerSource}
                    onChange={(e) => setArticlesPerSource(parseInt(e.target.value))}
                    className="article-slider"
                    disabled={loading}
                  />
                  <div className="selector-display">
                    <span className="current-value">{articlesPerSource}</span>
                    <span className="selector-text">articles per source</span>
                  </div>
                </div>
                <div className="selector-range">
                  <span>5</span>
                  <span>30</span>
                </div>
              </div>

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
              
              {/* Loading Progress Bar */}
              {loading && (
                <div className="loading-container">
                  <div className="loading-progress-bar">
                    <div 
                      className="loading-progress-fill" 
                      style={{ width: `${loadingProgress}%` }}
                    ></div>
                  </div>
                  <div className="loading-progress-text">
                    {loadingStep} ({loadingProgress}%)
                  </div>
                </div>
              )}
              
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

          {/* Time Range Selector */}
          <div className="time-range-selector">
            <button className={timeRange === 'today' ? 'active' : ''} onClick={() => setTimeRange('today')}>Today</button>
            <button className={timeRange === 'week' ? 'active' : ''} onClick={() => setTimeRange('week')}>Last 7 Days</button>
            <button className={timeRange === 'month' ? 'active' : ''} onClick={() => setTimeRange('month')}>Last 30 Days</button>
          </div>

          {/* Data Visualization Section */}
          {showCharts && newsData && (
            <section className="charts-section" ref={chartsRef}>
              <div className="charts-container">
                <h2>News Analysis Dashboard</h2>
                
                {/* Export Buttons */}
                <div className="export-buttons">
                  <h3>Export Data</h3>
                  <div className="export-button-group">
                    <button 
                      className="export-btn"
                      onClick={() => window.open(`${API_BASE_URL}/export/articles`, '_blank')}
                      title="Download article details with sentiment analysis"
                    >
                      📄 Articles CSV
                    </button>
                    <button 
                      className="export-btn"
                      onClick={() => window.open(`${API_BASE_URL}/export/sentiment`, '_blank')}
                      title="Download sentiment analysis summary"
                    >
                      😊 Sentiment CSV
                    </button>
                    <button 
                      className="export-btn"
                      onClick={() => window.open(`${API_BASE_URL}/export/trends`, '_blank')}
                      title="Download trending keywords analysis"
                    >
                      🔥 Trends CSV
                    </button>
                    <button 
                      className="export-btn"
                      onClick={() => window.open(`${API_BASE_URL}/export/complete`, '_blank')}
                      title="Download complete analysis report"
                    >
                      📊 Complete CSV
                    </button>
                    <button 
                      className="export-btn primary-export"
                      onClick={() => window.open(`${API_BASE_URL}/export/all`, '_blank')}
                      title="Download all data combined in one file"
                    >
                      📋 All Data CSV
                    </button>
                  </div>
                  <p className="export-note">
                    All exports are Excel-compatible with proper formatting and percentages
                  </p>
                </div>
                
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
                        <Tooltip 
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div style={{
                                  backgroundColor: 'rgba(0, 0, 0, 0.95)',
                                  border: `3px solid ${data.color}`,
                                  borderRadius: '12px',
                                  padding: '16px',
                                  boxShadow: '0 8px 25px rgba(0, 0, 0, 0.4)',
                                  color: 'white',
                                  fontSize: '14px',
                                  fontWeight: '500',
                                  minWidth: '180px'
                                }}>
                                  <div style={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    marginBottom: '8px',
                                    fontWeight: '600',
                                    fontSize: '16px'
                                  }}>
                                    <div style={{
                                      width: '12px',
                                      height: '12px',
                                      backgroundColor: data.color,
                                      borderRadius: '50%',
                                      marginRight: '8px'
                                    }}></div>
                                    {data.name} Sentiment
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Articles: <strong>{data.value}</strong>
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Percentage: <strong>{((data.value / prepareSentimentData().reduce((sum, item) => sum + item.value, 0)) * 100).toFixed(1)}%</strong>
                                  </div>
                                  <div style={{ 
                                    fontSize: '12px', 
                                    color: '#d1d5db',
                                    fontStyle: 'italic'
                                  }}>
                                    {data.name === 'Positive' ? '😊' : data.name === 'Negative' ? '😞' : '😐'} 
                                    {data.name === 'Positive' ? ' Positive coverage' : 
                                     data.name === 'Negative' ? ' Negative coverage' : ' Neutral coverage'}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
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
                        <Tooltip 
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              const totalArticles = prepareSourceData().reduce((sum, item) => sum + item.count, 0);
                              const percentage = ((data.count / totalArticles) * 100).toFixed(1);
                              return (
                                <div style={{
                                  backgroundColor: 'rgba(0, 0, 0, 0.95)',
                                  border: '3px solid #2563eb',
                                  borderRadius: '12px',
                                  padding: '16px',
                                  boxShadow: '0 8px 25px rgba(0, 0, 0, 0.4)',
                                  color: 'white',
                                  fontSize: '14px',
                                  fontWeight: '500',
                                  minWidth: '200px'
                                }}>
                                  <div style={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    marginBottom: '8px',
                                    fontWeight: '600',
                                    fontSize: '16px'
                                  }}>
                                    <div style={{
                                      width: '12px',
                                      height: '12px',
                                      backgroundColor: '#2563eb',
                                      borderRadius: '3px',
                                      marginRight: '8px'
                                    }}></div>
                                    {data.source} News
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Articles: <strong>{data.count}</strong>
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Percentage: <strong>{percentage}%</strong>
                                  </div>
                                  <div style={{ 
                                    fontSize: '12px', 
                                    color: '#d1d5db',
                                    fontStyle: 'italic'
                                  }}>
                                    📰 {data.source === 'BBC' ? 'British Broadcasting Corporation' : 
                                         data.source === 'CNN' ? 'Cable News Network' : 
                                         data.source === 'Reuters' ? 'Reuters News Agency' : 'News Source'}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Bar dataKey="count" fill="#2563eb" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Average Sentiment by Source */}
                  <div className="chart-card">
                    <h3>Average Sentiment by Source</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={prepareSentimentBySourceData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="source" />
                        <YAxis domain={[-1, 1]} />
                        <Tooltip 
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              const sentiment = data.avgSentiment;
                              const sentimentLabel = sentiment > 0.1 ? 'Positive' : sentiment < -0.1 ? 'Negative' : 'Neutral';
                              const sentimentEmoji = sentiment > 0.1 ? '😊' : sentiment < -0.1 ? '😞' : '😐';
                              const sentimentColor = sentiment > 0.1 ? '#10b981' : sentiment < -0.1 ? '#ef4444' : '#6b7280';
                              
                              return (
                                <div style={{
                                  backgroundColor: 'rgba(0, 0, 0, 0.95)',
                                  border: `3px solid ${sentimentColor}`,
                                  borderRadius: '12px',
                                  padding: '16px',
                                  boxShadow: '0 8px 25px rgba(0, 0, 0, 0.4)',
                                  color: 'white',
                                  fontSize: '14px',
                                  fontWeight: '500',
                                  minWidth: '220px'
                                }}>
                                  <div style={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    marginBottom: '8px',
                                    fontWeight: '600',
                                    fontSize: '16px'
                                  }}>
                                    <div style={{
                                      width: '12px',
                                      height: '12px',
                                      backgroundColor: sentimentColor,
                                      borderRadius: '50%',
                                      marginRight: '8px'
                                    }}></div>
                                    {data.source} Sentiment
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Score: <strong>{sentiment.toFixed(3)}</strong>
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Classification: <strong style={{ color: sentimentColor }}>{sentimentLabel}</strong>
                                  </div>
                                  <div style={{ 
                                    fontSize: '12px', 
                                    color: '#d1d5db',
                                    fontStyle: 'italic'
                                  }}>
                                    {sentimentEmoji} {sentimentLabel} coverage from {data.source}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Bar dataKey="avgSentiment" fill="#f59e42" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Temporal Trends */}
                  <div className="chart-card">
                    <h3>Temporal Trends</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={prepareTemporalTrendsData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="time" 
                          label={{ value: 'Time of Day', position: 'insideBottom', offset: -5 }}
                        />
                        <YAxis 
                          domain={[-1, 1]}
                          label={{ value: 'Average Sentiment', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div style={{
                                  backgroundColor: 'rgba(0, 0, 0, 0.95)',
                                  border: '3px solid #f59e42',
                                  borderRadius: '12px',
                                  padding: '16px',
                                  boxShadow: '0 8px 25px rgba(0, 0, 0, 0.4)',
                                  color: 'white',
                                  fontSize: '14px',
                                  fontWeight: '500',
                                  minWidth: '220px'
                                }}>
                                  <div style={{ 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    marginBottom: '8px',
                                    fontWeight: '600',
                                    fontSize: '16px'
                                  }}>
                                    <div style={{
                                      width: '12px',
                                      height: '12px',
                                      backgroundColor: '#f59e42',
                                      borderRadius: '50%',
                                      marginRight: '8px'
                                    }}></div>
                                    {data.time} - News Sentiment
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Articles: <strong>{data.articles}</strong>
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Avg Sentiment: <strong>{data.avgSentiment.toFixed(3)}</strong>
                                  </div>
                                  <div style={{ marginBottom: '4px' }}>
                                    Positive: <strong style={{ color: '#10b981' }}>{data.positive}</strong> | 
                                    Negative: <strong style={{ color: '#ef4444' }}>{data.negative}</strong> | 
                                    Neutral: <strong style={{ color: '#6b7280' }}>{data.neutral}</strong>
                                  </div>
                                  <div style={{ 
                                    fontSize: '12px', 
                                    color: '#d1d5db',
                                    fontStyle: 'italic'
                                  }}>
                                    📈 Sentiment trend at {data.time}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="avgSentiment" 
                          stroke="#f59e42" 
                          strokeWidth={3}
                          dot={{ fill: '#f59e42', strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6, stroke: '#f59e42', strokeWidth: 2 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Keyword Sentiment Analysis */}
                  <div className="chart-card">
                    <h3>Keyword Sentiment Analysis</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <ScatterChart data={prepareKeywordSentimentData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="frequency" 
                          name="Frequency" 
                          label={{ value: 'Keyword Frequency', position: 'insideBottom', offset: -5 }}
                        />
                        <YAxis 
                          dataKey="sentiment" 
                          name="Sentiment" 
                          domain={[-1, 1]}
                          label={{ value: 'Average Sentiment', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                          cursor={{ strokeDasharray: '3 3' }}
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div style={{
                                  backgroundColor: 'rgba(0, 0, 0, 0.9)',
                                  border: '2px solid #2563eb',
                                  borderRadius: '8px',
                                  padding: '12px',
                                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                                  color: 'white',
                                  fontSize: '14px',
                                  fontWeight: '500'
                                }}>
                                  <div style={{ marginBottom: '4px', fontWeight: '600', color: '#60a5fa' }}>
                                    Keyword: <strong>{data.keyword}</strong>
                                  </div>
                                  <div style={{ marginBottom: '2px' }}>
                                    Frequency: <strong>{data.frequency}</strong>
                                  </div>
                                  <div style={{ marginBottom: '2px' }}>
                                    Sentiment: <strong>{data.sentiment.toFixed(3)}</strong>
                                  </div>
                                  <div style={{ fontSize: '12px', color: '#d1d5db' }}>
                                    Articles: {data.articleCount}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Scatter 
                          dataKey="sentiment" 
                          fill="#8884d8"
                          r={6}
                        />
                      </ScatterChart>
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
                      return (
                        <ResponsiveContainer width="100%" height={chartHeight}>
                          <BarChart data={keywordData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" />
                            <YAxis dataKey="keyword" type="category" width={100} />
                            <Tooltip 
                              content={({ active, payload, label }) => {
                                if (active && payload && payload.length) {
                                  const data = payload[0].payload;
                                  const totalKeywords = keywordData.reduce((sum, item) => sum + item.count, 0);
                                  const percentage = ((data.count / totalKeywords) * 100).toFixed(1);
                                  const rank = keywordData.findIndex(item => item.keyword === data.keyword) + 1;
                                  
                                  return (
                                    <div style={{
                                      backgroundColor: 'rgba(0, 0, 0, 0.95)',
                                      border: '3px solid #10b981',
                                      borderRadius: '12px',
                                      padding: '16px',
                                      boxShadow: '0 8px 25px rgba(0, 0, 0, 0.4)',
                                      color: 'white',
                                      fontSize: '14px',
                                      fontWeight: '500',
                                      minWidth: '250px'
                                    }}>
                                      <div style={{ 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        marginBottom: '8px',
                                        fontWeight: '600',
                                        fontSize: '16px'
                                      }}>
                                        <div style={{
                                          width: '12px',
                                          height: '12px',
                                          backgroundColor: '#10b981',
                                          borderRadius: '3px',
                                          marginRight: '8px'
                                        }}></div>
                                        #{rank} Trending Keyword
                                      </div>
                                      <div style={{ marginBottom: '4px' }}>
                                        Keyword: <strong style={{ color: '#10b981' }}>"{data.keyword}"</strong>
                                      </div>
                                      <div style={{ marginBottom: '4px' }}>
                                        Mentions: <strong>{data.count}</strong>
                                      </div>
                                      <div style={{ marginBottom: '4px' }}>
                                        Share: <strong>{percentage}%</strong>
                                      </div>
                                      <div style={{ 
                                        fontSize: '12px', 
                                        color: '#d1d5db',
                                        fontStyle: 'italic'
                                      }}>
                                        🔥 {rank === 1 ? 'Most trending topic' : 
                                             rank <= 3 ? 'Top trending topic' : 
                                             rank <= 5 ? 'Popular topic' : 'Trending topic'}
                                      </div>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
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

          {/* Donate CTA Section */}
          <section className="donate-cta-section">
            <div className="donate-cta-container">
              <img src={process.env.PUBLIC_URL + '/donate_eth.avif'} alt="Donate ETH" className="donate-cta-image" />
              <div className="donate-cta-content">
                <h2>Support Us with a Donation</h2>
                <p>If you like this project and want to help us keep it free, consider making a donation. Every bit helps us improve and maintain the platform!</p>
                <button
                  className="primary-btn"
                  onClick={() => {
                    donationRef.current?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  Make a Donation
                </button>
              </div>
            </div>
          </section>

          {/* Newsletter Signup Section */}
          <NewsletterSignup />

          {/* FAQ Section */}
          <section className="faq-section" id="faq">
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

          {/* Footer Donation Section */}
          <div className="donation-section" ref={donationRef}>
            <img src={process.env.PUBLIC_URL + '/MetaMask-icon-fox-developer.svg'} alt="MetaMask" className="metamask-logo" />
            <h2>Support Our Project</h2>
            <p>
              Currently, this website is <b>free to use</b> because we are in beta. You can help us keep it free by donating SepoliaETH (testnet) using MetaMask.<br/>
              <span style={{color:'#2563eb'}}>Donations help us cover costs and improve the platform!</span>
            </p>
            <div className="donation-form">
              <input
                type="number"
                min="0"
                step="0.001"
                placeholder="Amount (SepoliaETH)"
                value={donationAmount}
                onChange={e => setDonationAmount(e.target.value)}
                disabled={donationLoading}
              />
              <button
                className="primary-btn"
                onClick={handleDonate}
                disabled={donationLoading}
              >
                {donationLoading ? 'Processing...' : 'Donate Now'}
              </button>
            </div>
            {donationStatus && (
              <div className={`donation-status${donationStatus.includes('Thank you') ? ' donation-success' : ''}${donationStatus.includes('MetaMask') ? ' donation-error' : ''}`}>
                {donationStatus.includes('MetaMask')
                  ? (donationStatus.includes('not installed')
                      ? 'You need MetaMask to make a donation.'
                      : 'Failed to connect to MetaMask.')
                  : donationStatus}
              </div>
            )}
            <div className="donation-note">
              <b>Note:</b> Only SepoliaETH (testnet) is accepted. No real ETH is used.
            </div>
          </div>

          {/* Main Footer Section */}
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
                    <li><button style={{background:'none',border:'none',color:'#cbd5e1',cursor:'pointer',padding:0}} onClick={() => {
                      if (window.location.pathname === '/') {
                        document.getElementById('faq')?.scrollIntoView({ behavior: 'smooth' });
                      } else {
                        navigate('/');
                        setTimeout(() => {
                          document.getElementById('faq')?.scrollIntoView({ behavior: 'smooth' });
                        }, 100);
                      }
                    }}>FAQ</button></li>
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
