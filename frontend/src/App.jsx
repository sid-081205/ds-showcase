import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Home from './pages/Home'
import Insights from './pages/Insights'
import Parties from './pages/Parties'
import Callback from './pages/Callback'
import axios from 'axios'

const API_URL = 'http://localhost:3001'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('spotify_access_token')
    const userId = localStorage.getItem('user_id')

    if (token && userId) {
      // Verify token is still valid
      axios.get(`${API_URL}/api/user/${userId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(response => {
        setUser(response.data)
      })
      .catch(() => {
        localStorage.removeItem('spotify_access_token')
        localStorage.removeItem('user_id')
      })
      .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const handleLogin = () => {
    window.location.href = `${API_URL}/auth/login`
  }

  const handleLogout = () => {
    localStorage.removeItem('spotify_access_token')
    localStorage.removeItem('user_id')
    setUser(null)
    navigate('/')
  }

  if (loading) {
    return <div className="loading">loading audire...</div>
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo">audire</div>
        <nav className="nav-links">
          <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
            home
          </Link>
          <Link to="/insights" className={`nav-link ${location.pathname === '/insights' ? 'active' : ''}`}>
            extracting insights
          </Link>
          <Link to="/parties" className={`nav-link ${location.pathname === '/parties' ? 'active' : ''}`}>
            creating parties
          </Link>
        </nav>
      </aside>

      <main className="main-content">
        <header className="header">
          <h1 className="page-title">
            {location.pathname === '/' && 'home'}
            {location.pathname === '/insights' && 'insights'}
            {location.pathname === '/parties' && 'parties'}
            {location.pathname === '/callback' && 'connecting...'}
          </h1>
          <div className="auth-section">
            {user ? (
              <>
                <span className="user-info">welcome, {user.display_name}</span>
                <button onClick={handleLogout} className="auth-button logout">
                  logout
                </button>
              </>
            ) : (
              <button onClick={handleLogin} className="auth-button">
                connect spotify
              </button>
            )}
          </div>
        </header>

        <Routes>
          <Route path="/" element={<Home user={user} />} />
          <Route path="/insights" element={<Insights user={user} />} />
          <Route path="/parties" element={<Parties user={user} />} />
          <Route path="/callback" element={<Callback setUser={setUser} />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
