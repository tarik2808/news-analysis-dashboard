import React, { useEffect, useState } from 'react';

export default function NewsletterSignup() {
  const [newsletterEmail, setNewsletterEmail] = useState('');
  const [newsletterStatus, setNewsletterStatus] = useState('');
  const [newsletterStatusType, setNewsletterStatusType] = useState(''); // 'success', 'error', 'info'

  // Handler for newsletter signup
  const handleNewsletterSignup = async (e) => {
    e.preventDefault();
    setNewsletterStatus('Submitting...');
    setNewsletterStatusType('info');
    try {
      const res = await fetch('http://localhost:8000/newsletter/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newsletterEmail })
      });
      const data = await res.json();
      if (res.ok) {
        setNewsletterStatus(data.message || 'Check your email for verification!');
        setNewsletterStatusType('success');
        setNewsletterEmail('');
      } else {
        if (res.status === 400 && data.detail) {
          if (data.detail.includes('already subscribed')) {
            setNewsletterStatus('✅ You\'re already subscribed! Check your email for verification.');
            setNewsletterStatusType('success');
            setNewsletterEmail('');
          } else {
            setNewsletterStatus(`Error: ${data.detail}`);
            setNewsletterStatusType('error');
          }
        } else if (res.status === 422 && data.detail) {
          setNewsletterStatus(`Please enter a valid email address.`);
          setNewsletterStatusType('error');
        } else {
          setNewsletterStatus(data.detail || 'Could not subscribe. Please try again.');
          setNewsletterStatusType('error');
        }
      }
    } catch (err) {
      setNewsletterStatus('Error: Could not subscribe. Please try again.');
      setNewsletterStatusType('error');
    }
  };

  // Clear status after a delay
  useEffect(() => {
    if (newsletterStatusType === 'success' && newsletterStatus) {
      const timer = setTimeout(() => {
        setNewsletterStatus('');
        setNewsletterStatusType('');
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [newsletterStatusType, newsletterStatus]);

  return (
    <section className="newsletter-section">
      <div className="newsletter-container card-horizontal">
        <img src="/envelope.png" alt="Newsletter Envelope" className="newsletter-image" />
        <div className="newsletter-content">
          <h2>Join Our Newsletter</h2>
          <p>Get a weekly summary of the hottest news, straight to your inbox!</p>
          <form onSubmit={handleNewsletterSignup} className="newsletter-form">
            <input
              type="email"
              placeholder="Enter your email"
              value={newsletterEmail}
              onChange={e => setNewsletterEmail(e.target.value)}
              className="newsletter-input"
              required
            />
            <button type="submit" className="primary-btn">Subscribe</button>
          </form>
          {newsletterStatus && (
            <div className={`newsletter-status${
              newsletterStatusType === 'error' ? ' error' :
              newsletterStatusType === 'success' ? '' :
              newsletterStatusType === 'info' ? ' info' : ''
            }`}>
              {newsletterStatus}
            </div>
          )}
        </div>
      </div>
    </section>
  );
} 