import { useNavigate } from 'react-router-dom'

function Home({ user }) {
  const navigate = useNavigate()

  return (
    <div className="home-page">
      <div className="card">
        <h2 className="card-title">welcome to audire</h2>
        <div className="card-content">
          <p style={{ marginBottom: '16px' }}>
            discover how your music taste tells a story. audire analyzes your spotify listening history
            to reveal the mood, energy, and vibe of your musical journey.
          </p>
          <p style={{ marginBottom: '16px' }}>
            see how your emotions flow through the songs you love, track your musical evolution over time,
            and find out how your taste connects with your friends.
          </p>
          {!user && (
            <p style={{ color: 'var(--spotify-green)' }}>
              connect your spotify account to get started.
            </p>
          )}
        </div>
      </div>

      {user && (
        <div className="grid">
          <div className="stat-card" onClick={() => navigate('/insights')} style={{ cursor: 'pointer' }}>
            <div className="stat-value">∞</div>
            <div className="stat-label">your music insights</div>
          </div>

          <div className="stat-card" onClick={() => navigate('/parties')} style={{ cursor: 'pointer' }}>
            <div className="stat-value">+</div>
            <div className="stat-label">create a party</div>
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">features</h2>
        <div className="card-content">
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li style={{ marginBottom: '12px' }}>→ mood progression tracking over 6 months</li>
            <li style={{ marginBottom: '12px' }}>→ energy and vibe analysis of your top songs</li>
            <li style={{ marginBottom: '12px' }}>→ listening pattern insights</li>
            <li style={{ marginBottom: '12px' }}>→ multi-user party mode for group analysis</li>
            <li style={{ marginBottom: '12px' }}>→ music taste correlation between friends</li>
            <li>→ anytime spotify wrapped experience</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default Home
