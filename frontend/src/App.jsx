import { useState, useEffect } from 'react';
import WelcomePage from './components/WelcomePage';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check karo agar user pehle se logged in hai
  useEffect(() => {
    if (localStorage.getItem('token')) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setIsAuthenticated(false);
  };

  return (
    <div>
      {isAuthenticated ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <WelcomePage onAuthSuccess={() => setIsAuthenticated(true)} />
      )}
    </div>
  );
}

export default App;