import React, { useState, useEffect } from 'react';
import './InvestmentDashboard.css';

const InvestmentDashboard = () => {
  const [analyses, setAnalyses] = useState([]);
  const [blogPosts, setBlogPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTickers, setSelectedTickers] = useState('AAPL,GOOGL,MSFT');
  const [blogTopic, setBlogTopic] = useState('Market Analysis');

  const API_BASE = 'http://localhost:8000/api/v1';

  const fetchStockAnalyses = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/investment/stocks?tickers=${selectedTickers}`);
      const data = await response.json();
      setAnalyses(data.analyses || []);
    } catch (error) {
      console.error('Error fetching analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateBlogPost = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/investment/blog/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tickers: selectedTickers,
          topic: blogTopic
        })
      });
      const data = await response.json();
      
      if (data.blog_post) {
        alert('Blog post generated successfully!');
        fetchBlogPosts();
      }
    } catch (error) {
      console.error('Error generating blog:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBlogPosts = async () => {
    try {
      const response = await fetch(`${API_BASE}/investment/blog/posts`);
      const data = await response.json();
      setBlogPosts(data.posts || []);
    } catch (error) {
      console.error('Error fetching blog posts:', error);
    }
  };

  useEffect(() => {
    fetchBlogPosts();
  }, []);

  return (
    <div className="investment-dashboard">
      <header className="dashboard-header">
        <h1>AI Investment Blog Assistant</h1>
        <p>Automated investment analysis and blog generation</p>
      </header>

      <div className="dashboard-content">
        {/* Controls Section */}
        <div className="controls-section">
          <div className="control-group">
            <label>Stock Tickers (comma-separated):</label>
            <input
              type="text"
              value={selectedTickers}
              onChange={(e) => setSelectedTickers(e.target.value)}
              placeholder="AAPL,GOOGL,MSFT"
            />
          </div>
          
          <div className="control-group">
            <label>Blog Topic:</label>
            <input
              type="text"
              value={blogTopic}
              onChange={(e) => setBlogTopic(e.target.value)}
              placeholder="Market Analysis"
            />
          </div>

          <div className="action-buttons">
            <button 
              onClick={fetchStockAnalyses} 
              disabled={loading}
              className="btn-primary"
            >
              {loading ? 'Analyzing...' : 'Analyze Stocks'}
            </button>
            
            <button 
              onClick={generateBlogPost} 
              disabled={loading}
              className="btn-secondary"
            >
              {loading ? 'Generating...' : 'Generate Blog Post'}
            </button>
          </div>
        </div>

        {/* Stock Analyses Section */}
        {analyses.length > 0 && (
          <div className="analyses-section">
            <h2>Stock Analyses</h2>
            <div className="analyses-grid">
              {analyses.map((analysis, index) => (
                <div key={index} className="analysis-card">
                  <div className="analysis-header">
                    <h3>{analysis.ticker}</h3>
                    <span className={`recommendation ${analysis.recommendation}`}>
                      {analysis.recommendation.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="analysis-data">
                    <div className="data-row">
                      <span>Price:</span>
                      <span>${analysis.stock_data.price?.toFixed(2)}</span>
                    </div>
                    <div className="data-row">
                      <span>30d Change:</span>
                      <span className={analysis.technical_indicators.price_change_pct >= 0 ? 'positive' : 'negative'}>
                        {analysis.technical_indicators.price_change_pct?.toFixed(2)}%
                      </span>
                    </div>
                    <div className="data-row">
                      <span>RSI:</span>
                      <span>{analysis.technical_indicators.rsi?.toFixed(2)}</span>
                    </div>
                    <div className="data-row">
                      <span>Confidence:</span>
                      <span>{(analysis.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  
                  <div className="analysis-summary">
                    <p>{analysis.ai_analysis?.substring(0, 150)}...</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Blog Posts Section */}
        <div className="blog-posts-section">
          <h2>Generated Blog Posts</h2>
          {blogPosts.length === 0 ? (
            <p>No blog posts generated yet. Click "Generate Blog Post" to create one.</p>
          ) : (
            <div className="blog-posts-list">
              {blogPosts.map((post) => (
                <div key={post.id} className="blog-post-card">
                  <h3>{post.title}</h3>
                  <div className="post-meta">
                    <span>Tickers: {post.tickers_analyzed}</span>
                    <span>Words: {post.word_count}</span>
                    <span>Created: {new Date(post.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="post-summary">{post.summary}</p>
                  <button 
                    className="btn-link"
                    onClick={() => window.open(`${API_BASE}/investment/blog/posts/${post.id}`, '_blank')}
                  >
                    View Full Post
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InvestmentDashboard;