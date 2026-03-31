import React, { useState } from 'react';
import axios from 'axios';
import './WelcomePage.css';

// 🌟 NAYA: Dynamic Card (Login aur Signup dono ka kaam karega)
const AuthCard = ({ isLoginView, username, setUsername, password, setPassword, onSubmit, loading }) => (
  <div className="signup-card">
    <div className="card-header">{isLoginView ? 'Login' : 'Signup'}</div>
    <form className="form-group" onSubmit={onSubmit}>
      <div className="form-item">
        <label className="card-label" htmlFor="username">User Name</label>
        <input 
          id="username"
          type="text" 
          className="form-input" 
          placeholder="Enter username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </div>
      <div className="form-item">
        <label className="card-label" htmlFor="password">Password</label>
        <input 
          id="password"
          type="password" 
          className="form-input" 
          placeholder="Enter password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <button type="submit" className="submit-button" disabled={loading}>
        {loading ? 'Wait...' : 'Submit'}
      </button>
    </form>
    <div className="social-icons">
      <i className="fa fa-facebook"></i>
      <i className="fa fa-instagram"></i>
      <i className="fa fa-pinterest"></i>
    </div>
  </div>
);

const WelcomePage = ({ onAuthSuccess }) => {
  // 🌟 NAYA: States for Logic
  const [isLoginView, setIsLoginView] = useState(false); // Default Signup dikhega
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // 🌟 NAYA: API Call Logic (Jo tumne pehle likha tha)
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isLoginView) {
        // --- LOGIN LOGIC ---
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        const response = await axios.post('http://127.0.0.1:8000/login', params, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('username', username);
        onAuthSuccess(); // App.jsx ko batao ki login ho gaya!
      } else {
        // --- SIGNUP LOGIC ---
        const response = await axios.post('http://127.0.0.1:8000/signup', { username, password });
        alert(response.data.message + " Please login now.");
        setIsLoginView(true); // Signup ke baad Login form dikhao
        setPassword(''); 
      }
    } catch (error) {
      alert(error.response?.data?.detail || "Something went wrong!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="welcome-page">
      <div className="li-logo">Li</div>

      <div className="welcome-content">
        <div className="welcome-left">
          <h1 className="welcome-header">Welcome!</h1>
          <div className="welcome-divider"></div>
          <p className="welcome-text">
            turn any github repo into a conversation
          </p>
          <div className="welcome-divider"></div>
          {/* 🌟 NAYA: Toggle Button */}
          <button 
            className="login-button" 
            onClick={() => setIsLoginView(!isLoginView)}
          >
            {isLoginView ? 'Signup' : 'Login'}
          </button>
        </div>

        <div className="welcome-right">
          <AuthCard 
            isLoginView={isLoginView}
            username={username}
            setUsername={setUsername}
            password={password}
            setPassword={setPassword}
            onSubmit={handleSubmit}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
};

export default WelcomePage;