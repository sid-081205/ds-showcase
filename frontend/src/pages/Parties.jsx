import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts'

const API_URL = 'http://localhost:3001'

function Parties({ user }) {
  const [parties, setParties] = useState([])
  const [activeParty, setActiveParty] = useState(null)
  const [partyInsights, setPartyInsights] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [partyName, setPartyName] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      fetchParties()
    }
  }, [user])

  const fetchParties = async () => {
    try {
      const token = localStorage.getItem('spotify_access_token')
      const response = await axios.get(`${API_URL}/api/parties/user/${user.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      setParties(response.data)
    } catch (error) {
      console.error('Failed to fetch parties:', error)
    }
  }

  const createParty = async () => {
    if (!partyName.trim()) return

    try {
      const token = localStorage.getItem('spotify_access_token')
      const response = await axios.post(
        `${API_URL}/api/parties`,
        { name: partyName, creatorId: user.id },
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      setParties([...parties, response.data])
      setPartyName('')
      setShowCreateForm(false)
    } catch (error) {
      console.error('Failed to create party:', error)
    }
  }

  const joinParty = async (partyId) => {
    try {
      const token = localStorage.getItem('spotify_access_token')
      await axios.post(
        `${API_URL}/api/parties/${partyId}/join`,
        { userId: user.id },
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      fetchParties()
    } catch (error) {
      console.error('Failed to join party:', error)
    }
  }

  const viewPartyInsights = async (partyId) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('spotify_access_token')
      const response = await axios.get(`${API_URL}/api/parties/${partyId}/insights`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      setPartyInsights(response.data)
      setActiveParty(partyId)
    } catch (error) {
      console.error('Failed to fetch party insights:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    return (
      <div className="card">
        <h2 className="card-title">connect spotify</h2>
        <div className="card-content">
          please connect your spotify account to create or join parties.
        </div>
      </div>
    )
  }

  if (activeParty && partyInsights) {
    return (
      <div className="party-insights-page">
        <button
          onClick={() => { setActiveParty(null); setPartyInsights(null); }}
          className="button-secondary"
          style={{ marginBottom: '24px' }}
        >
          ← back to parties
        </button>

        {loading ? (
          <div className="loading">analyzing party vibes...</div>
        ) : (
          <>
            {/* Party Stats */}
            <div className="grid">
              <div className="stat-card">
                <div className="stat-value">{partyInsights.members?.length || 0}</div>
                <div className="stat-label">members</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">
                  {(partyInsights.compatibility * 100).toFixed(0)}%
                </div>
                <div className="stat-label">group compatibility</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{partyInsights.commonArtists?.length || 0}</div>
                <div className="stat-label">shared artists</div>
              </div>
            </div>

            {/* Member Comparisons Radar */}
            <div className="chart-container">
              <h3 className="chart-title">vibe comparison</h3>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={partyInsights.radarData}>
                  <PolarGrid stroke="#404040" />
                  <PolarAngleAxis
                    dataKey="feature"
                    stroke="#B3B3B3"
                    style={{ fontSize: '11px', fontVariant: 'small-caps' }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 1]}
                    stroke="#B3B3B3"
                  />
                  {partyInsights.members?.map((member, index) => {
                    const colors = ['#1DB954', '#1ed760', '#3BE477', '#5AF19A', '#79FFBD']
                    return (
                      <Radar
                        key={member.id}
                        name={member.display_name}
                        dataKey={`user_${member.id}`}
                        stroke={colors[index % colors.length]}
                        fill={colors[index % colors.length]}
                        fillOpacity={0.3}
                      />
                    )
                  })}
                  <Legend wrapperStyle={{ fontSize: '11px', fontVariant: 'small-caps' }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Mood Alignment Over Time */}
            <div className="chart-container">
              <h3 className="chart-title">mood alignment over time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={partyInsights.moodAlignment}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis
                    dataKey="month"
                    stroke="#B3B3B3"
                    style={{ fontSize: '11px', fontVariant: 'small-caps' }}
                  />
                  <YAxis
                    stroke="#B3B3B3"
                    style={{ fontSize: '11px' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#191414',
                      border: '1px solid #404040',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontVariant: 'small-caps'
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', fontVariant: 'small-caps' }} />
                  {partyInsights.members?.map((member, index) => {
                    const colors = ['#1DB954', '#1ed760', '#3BE477', '#5AF19A', '#79FFBD']
                    return (
                      <Line
                        key={member.id}
                        type="monotone"
                        dataKey={`user_${member.id}`}
                        stroke={colors[index % colors.length]}
                        strokeWidth={2}
                        name={member.display_name}
                      />
                    )
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Common Artists */}
            <div className="card">
              <h2 className="card-title">shared music taste</h2>
              <div className="card-content">
                {partyInsights.commonArtists?.length > 0 ? (
                  partyInsights.commonArtists.map((artist, index) => (
                    <div key={index} style={{
                      marginBottom: '12px',
                      paddingBottom: '12px',
                      borderBottom: index < partyInsights.commonArtists.length - 1 ? '1px solid #282828' : 'none'
                    }}>
                      <span style={{ color: '#1DB954', marginRight: '12px' }}>{index + 1}.</span>
                      {artist.name}
                      <span style={{ marginLeft: '12px', color: '#B3B3B3', fontSize: '11px' }}>
                        loved by {artist.sharedBy} members
                      </span>
                    </div>
                  ))
                ) : (
                  <p>no shared artists yet. everyone has unique taste!</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="parties-page">
      <div style={{ marginBottom: '24px' }}>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="button-primary"
        >
          {showCreateForm ? 'cancel' : '+ create party'}
        </button>
      </div>

      {showCreateForm && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 className="card-title">create new party</h2>
          <div className="card-content">
            <input
              type="text"
              placeholder="party name"
              value={partyName}
              onChange={(e) => setPartyName(e.target.value)}
              style={{ marginBottom: '16px' }}
            />
            <button onClick={createParty} className="button-primary">
              create
            </button>
          </div>
        </div>
      )}

      <div className="party-grid">
        {parties.length === 0 ? (
          <div className="card">
            <h2 className="card-title">no parties yet</h2>
            <div className="card-content">
              create your first party to compare music tastes with friends!
            </div>
          </div>
        ) : (
          parties.map((party) => (
            <div key={party.id} className="party-card">
              <div className="party-name">{party.name}</div>
              <div className="party-members">
                {party.member_count || 1} member{party.member_count !== 1 ? 's' : ''}
              </div>
              <button
                onClick={() => viewPartyInsights(party.id)}
                className="button-primary"
                style={{ width: '100%', marginBottom: '8px' }}
              >
                view insights
              </button>
              {!party.is_member && (
                <button
                  onClick={() => joinParty(party.id)}
                  className="button-secondary"
                  style={{ width: '100%' }}
                >
                  join party
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default Parties
