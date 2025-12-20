import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis
} from 'recharts'

const API_URL = 'http://localhost:3001'

function Insights({ user }) {
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user) {
      fetchInsights()
    } else {
      setLoading(false)
    }
  }, [user])

  const fetchInsights = async () => {
    try {
      const token = localStorage.getItem('spotify_access_token')
      const response = await axios.get(`${API_URL}/api/insights/${user.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      setInsights(response.data)
    } catch (error) {
      console.error('Failed to fetch insights:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!user) {
    return (
      <div className="card">
        <h2 className="card-title">connect spotify</h2>
        <div className="card-content">
          please connect your spotify account to view insights.
        </div>
      </div>
    )
  }

  if (loading) {
    return <div className="loading">analyzing your music...</div>
  }

  if (!insights || !insights.audioFeatures) {
    return (
      <div className="card">
        <h2 className="card-title">no data yet</h2>
        <div className="card-content">
          we're still processing your listening history. this may take a moment.
          <br /><br />
          <button onClick={fetchInsights} className="button-primary">
            refresh
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="insights-page">
      {/* Stats Overview */}
      <div className="grid">
        <div className="stat-card">
          <div className="stat-value">{insights.stats?.totalTracks || 0}</div>
          <div className="stat-label">tracks analyzed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{insights.stats?.totalArtists || 0}</div>
          <div className="stat-label">unique artists</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{insights.stats?.totalPlaylists || 0}</div>
          <div className="stat-label">playlists</div>
        </div>
      </div>

      {/* Mood Progression Over Time */}
      <div className="chart-container">
        <h3 className="chart-title">mood progression (6 months)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={insights.moodProgression}>
            <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
            <XAxis
              dataKey="month"
              stroke="#B3B3B3"
              style={{ fontSize: '11px', fontVariant: 'small-caps' }}
            />
            <YAxis
              stroke="#B3B3B3"
              style={{ fontSize: '11px', fontVariant: 'small-caps' }}
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
            <Legend
              wrapperStyle={{ fontSize: '11px', fontVariant: 'small-caps' }}
            />
            <Line
              type="monotone"
              dataKey="valence"
              stroke="#1DB954"
              strokeWidth={2}
              name="happiness"
              dot={{ fill: '#1DB954', r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="energy"
              stroke="#1ed760"
              strokeWidth={2}
              name="energy"
              dot={{ fill: '#1ed760', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Audio Features Radar */}
      <div className="chart-container">
        <h3 className="chart-title">your music vibe profile</h3>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={insights.audioFeatures}>
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
              style={{ fontSize: '10px' }}
            />
            <Radar
              name="your average"
              dataKey="value"
              stroke="#1DB954"
              fill="#1DB954"
              fillOpacity={0.6}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Genre Distribution */}
      <div className="chart-container">
        <h3 className="chart-title">top genres</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={insights.genres}>
            <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
            <XAxis
              dataKey="genre"
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
            <Bar dataKey="count" fill="#1DB954" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Energy vs Valence Scatter */}
      <div className="chart-container">
        <h3 className="chart-title">energy vs happiness scatter</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
            <XAxis
              type="number"
              dataKey="energy"
              name="energy"
              stroke="#B3B3B3"
              domain={[0, 1]}
              style={{ fontSize: '11px', fontVariant: 'small-caps' }}
            />
            <YAxis
              type="number"
              dataKey="valence"
              name="happiness"
              stroke="#B3B3B3"
              domain={[0, 1]}
              style={{ fontSize: '11px', fontVariant: 'small-caps' }}
            />
            <ZAxis range={[60, 400]} />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{
                backgroundColor: '#191414',
                border: '1px solid #404040',
                borderRadius: '4px',
                fontSize: '11px',
                fontVariant: 'small-caps'
              }}
            />
            <Scatter
              name="tracks"
              data={insights.scatterData}
              fill="#1DB954"
              opacity={0.6}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {/* Top Artists */}
      <div className="card">
        <h2 className="card-title">top artists</h2>
        <div className="card-content">
          {insights.topArtists?.map((artist, index) => (
            <div key={index} style={{
              marginBottom: '12px',
              paddingBottom: '12px',
              borderBottom: index < insights.topArtists.length - 1 ? '1px solid #282828' : 'none'
            }}>
              <span style={{ color: '#1DB954', marginRight: '12px' }}>{index + 1}.</span>
              {artist.name}
              <span style={{ marginLeft: '12px', color: '#B3B3B3', fontSize: '11px' }}>
                {artist.count} tracks
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Insights
