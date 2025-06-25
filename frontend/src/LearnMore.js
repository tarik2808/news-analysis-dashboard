import React from "react";

export default function LearnMore() {
  return (
    <>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "80vh", background: "#f7fafc", padding: "2rem" }}>
        {/* Left: Text Content */}
        <div style={{ flex: 1, maxWidth: 600, marginRight: 40 }}>
          <h2 style={{ fontSize: "2.5rem", marginBottom: 16, color: "#1a202c" }}>About the News Analysis Dashboard</h2>
          <p style={{ fontSize: "1.2rem", color: "#374151", marginBottom: 24 }}>
            This dashboard scrapes news from top sources, analyzes sentiment and trending keywords, and visualizes trends in real time. Built with FastAPI and React, it's designed for journalists, researchers, and data enthusiasts.
          </p>
          <ul style={{ fontSize: "1.1rem", color: "#2d3748", marginBottom: 24, paddingLeft: 24 }}>
            <li>Real-time news scraping from BBC, CNN, and more</li>
            <li>Sentiment and keyword analysis using NLP</li>
            <li>Interactive charts and trend visualizations</li>
            <li>Open source, extensible, and easy to deploy</li>
          </ul>
          <p style={{ color: "#4b5563" }}>
            Whether you're a data enthusiast, journalist, or researcher, discover smarter ways to explore the news—together.
          </p>
        </div>
        {/* Right: Image Box - fit to image */}
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <img src="/learnabout.png" alt="Learn More" style={{ width: '100%', maxWidth: 480, height: 'auto', borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.04)', background: '#e5e7eb', objectFit: 'contain' }} />
        </div>
      </div>
      {/* Footer copied from dashboard */}
      <div className="dashboard-footer">
        <div className="footer-container">
          <div className="footer-content">
            <div className="footer-section">
              <h3>News Analysis Platform</h3>
              <p>Your all-in-one solution for real-time news insights, sentiment analysis, and trend discovery from top international sources.</p>
            </div>
            <div className="footer-section">
              <h4>Quick Links</h4>
              <ul>
                <li><a href="#dashboard">Dashboard</a></li>
                <li><a href="#sentiment">Sentiment Analysis</a></li>
                <li><a href="#trends">Trending Topics</a></li>
                <li><a href="#faq">FAQ</a></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Contact</h4>
              <ul>
                <li><a href="mailto:contact@newsanalysis.com">contact@newsanalysis.com</a></li>
                <li><a href="https://github.com/yourusername" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                <li><a href="https://linkedin.com/in/yourusername" target="_blank" rel="noopener noreferrer">LinkedIn</a></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2024 News Analysis Platform. Built with React and FastAPI.</p>
          </div>
        </div>
      </div>
    </>
  );
} 