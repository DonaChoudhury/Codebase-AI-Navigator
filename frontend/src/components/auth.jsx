import { useState } from 'react';
import axios from 'axios';

function Auth({ onLogin }) {
  // State: 'landing' (default), 'login', ya 'signup'
  const [view, setView] = useState('landing'); 
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (view === 'login') {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        const response = await axios.post('http://127.0.0.1:8000/login', params, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('username', username);
        onLogin(); 
      } else if (view === 'signup') {
        const response = await axios.post('http://127.0.0.1:8000/signup', { username, password });
        alert(response.data.message + " Please sign in now.");
        setView('login'); // Signup successful hote hi Login card dikhao
        setPassword(''); // Password clear kar do safety ke liye
      }
    } catch (error) {
      alert(error.response?.data?.detail || "Something went wrong!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing-wrapper">
      
      {/* SCREEN 1: THE LANDING PAGE */}
      {view === 'landing' && (
        <div className="hero-text">
          <h1>Codebase RAG AI</h1>
          <p>
            The ultimate developer tool. Explore, chat with, and auto-document any GitHub repository in seconds using the power of AI.
          </p>
          <div className="action-buttons">
            <button className="btn-landing-primary" onClick={() => setView('login')}>
              Sign In
            </button>
            <button className="btn-landing-outline" onClick={() => setView('signup')}>
              Create Account
            </button>
          </div>
        </div>
      )}

      {/* SCREEN 2: THE GLASS CARD (Login / Signup) */}
      {(view === 'login' || view === 'signup') && (
        <div className="auth-card">
          <div className="back-btn" onClick={() => setView('landing')}>
            ← Back to Home
          </div>
          
          <h2>{view === 'login' ? 'Welcome Back 👋' : 'Join the Future 🚀'}</h2>
          
          <form onSubmit={handleSubmit}>
            <input 
              className="input-field" 
              type="text" 
              placeholder="Username" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              required 
            />
            <input 
              className="input-field" 
              type="password" 
              placeholder="Password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
            />
            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? 'Processing...' : (view === 'login' ? 'Sign In to Dashboard' : 'Create Account')}
            </button>
          </form>

          <p style={{ marginTop: '25px', color: '#94a3b8', fontSize: '14.5px' }}>
            {view === 'login' ? "Don't have an account? " : "Already have an account? "}
            <span 
              style={{ color: '#c084fc', fontWeight: '600', cursor: 'pointer' }} 
              onClick={() => setView(view === 'login' ? 'signup' : 'login')}
            >
              {view === 'login' ? "Sign Up" : "Sign In"}
            </span>
          </p>
        </div>
      )}

    </div>
  );
}

export default Auth;