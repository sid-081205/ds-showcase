import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import crypto from 'crypto'
import db, { initializeDatabase } from './database.js'
import * as spotify from './spotify.js'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 3001

app.use(cors())
app.use(express.json())

// Initialize database
await initializeDatabase()

// Auth routes
app.get('/auth/login', (req, res) => {
  const authUrl = spotify.getAuthorizationUrl()
  res.redirect(authUrl)
})

app.post('/auth/callback', async (req, res) => {
  try {
    const { code } = req.body

    // Exchange code for tokens
    const tokenData = await spotify.exchangeCodeForToken(code)
    const { access_token, refresh_token } = tokenData

    // Get user profile
    const profile = await spotify.getUserProfile(access_token)

    // Store or update user in database
    const userId = crypto.randomUUID()
    await db.runAsync(
      `INSERT OR REPLACE INTO users (id, spotify_id, display_name, email, access_token, refresh_token)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [userId, profile.id, profile.display_name, profile.email, access_token, refresh_token]
    )

    // Fetch and store user data in background
    fetchAndStoreUserData(userId, access_token).catch(console.error)

    res.json({
      access_token,
      user: {
        id: userId,
        spotify_id: profile.id,
        display_name: profile.display_name,
        email: profile.email
      }
    })
  } catch (error) {
    console.error('Auth callback error:', error)
    res.status(500).json({ error: 'Authentication failed' })
  }
})

// Fetch and store all user data
async function fetchAndStoreUserData(userId, accessToken) {
  try {
    const trackIds = new Set()

    console.log(`Starting comprehensive data fetch for user ${userId}`)

    // Get top tracks for ALL time ranges
    const timeRanges = ['short_term', 'medium_term', 'long_term']
    for (const range of timeRanges) {
      try {
        console.log(`Fetching top tracks for ${range}...`)
        const topTracks = await spotify.getTopTracks(accessToken, range, 50)

        for (const track of topTracks) {
          trackIds.add(track.id)

          // Store track
          await db.runAsync(
            `INSERT OR IGNORE INTO tracks (id, name, artist, album, duration_ms, popularity)
             VALUES (?, ?, ?, ?, ?, ?)`,
            [
              track.id,
              track.name,
              track.artists[0]?.name || 'Unknown',
              track.album.name,
              track.duration_ms,
              track.popularity
            ]
          )

          // Link track to user
          await db.runAsync(
            `INSERT OR IGNORE INTO user_tracks (user_id, track_id, played_at)
             VALUES (?, ?, CURRENT_TIMESTAMP)`,
            [userId, track.id]
          )
        }
        console.log(`Stored ${topTracks.length} tracks for ${range}`)
      } catch (error) {
        console.error(`Failed to fetch top tracks for ${range}:`, error.message)
      }
    }

    // Get recently played tracks (last 50)
    try {
      console.log('Fetching recently played tracks...')
      const recentTracks = await spotify.getRecentlyPlayed(accessToken, 50)

      for (const item of recentTracks) {
        const track = item.track
        trackIds.add(track.id)

        // Store track
        await db.runAsync(
          `INSERT OR IGNORE INTO tracks (id, name, artist, album, duration_ms, popularity)
           VALUES (?, ?, ?, ?, ?, ?)`,
          [
            track.id,
            track.name,
            track.artists[0]?.name || 'Unknown',
            track.album.name,
            track.duration_ms,
            track.popularity
          ]
        )

        // Link track to user with actual played_at timestamp
        await db.runAsync(
          `INSERT OR IGNORE INTO user_tracks (user_id, track_id, played_at)
           VALUES (?, ?, ?)`,
          [userId, track.id, item.played_at]
        )
      }
      console.log(`Stored ${recentTracks.length} recently played tracks`)
    } catch (error) {
      console.error('Failed to fetch recently played tracks:', error.message)
    }

    // Get audio features for all tracks
    const trackIdArray = Array.from(trackIds)
    if (trackIdArray.length > 0) {
      try {
        console.log(`Fetching audio features for ${trackIdArray.length} unique tracks...`)
        const audioFeatures = await spotify.getAudioFeatures(accessToken, trackIdArray)
        for (const features of audioFeatures) {
          if (features && features.id) {
            await db.runAsync(
              `INSERT OR REPLACE INTO audio_features
               (track_id, danceability, energy, loudness, speechiness, acousticness,
                instrumentalness, liveness, valence, tempo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
              [
                features.id,
                features.danceability || 0.5,
                features.energy || 0.5,
                features.loudness || -10,
                features.speechiness || 0.1,
                features.acousticness || 0.5,
                features.instrumentalness || 0.1,
                features.liveness || 0.2,
                features.valence || 0.5,
                features.tempo || 120
              ]
            )
          }
        }
        console.log(`Stored audio features for ${audioFeatures.length} tracks`)
      } catch (audioError) {
        console.error('Failed to fetch audio features, generating defaults:', audioError.message)
        // Generate default audio features for tracks if API fails
        for (const trackId of trackIdArray) {
          await db.runAsync(
            `INSERT OR IGNORE INTO audio_features
             (track_id, danceability, energy, loudness, speechiness, acousticness,
              instrumentalness, liveness, valence, tempo)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [trackId, 0.6, 0.6, -8, 0.1, 0.3, 0.1, 0.2, 0.6, 120]
          )
        }
        console.log(`Generated default audio features for ${trackIdArray.length} tracks`)
      }
    }

    // Get top artists for ALL time ranges
    for (const range of timeRanges) {
      try {
        console.log(`Fetching top artists for ${range}...`)
        const topArtists = await spotify.getTopArtists(accessToken, range, 50)
        for (const artist of topArtists) {
          // Store artist
          await db.runAsync(
            `INSERT OR IGNORE INTO artists (id, name, genres, popularity)
             VALUES (?, ?, ?, ?)`,
            [artist.id, artist.name, JSON.stringify(artist.genres), artist.popularity]
          )

          // Link artist to user
          await db.runAsync(
            `INSERT OR IGNORE INTO user_artists (user_id, artist_id)
             VALUES (?, ?)`,
            [userId, artist.id]
          )
        }
        console.log(`Stored ${topArtists.length} top artists for ${range}`)
      } catch (artistError) {
        console.error(`Failed to fetch top artists for ${range}:`, artistError.message)
      }
    }

    // Get playlists
    try {
      const playlists = await spotify.getUserPlaylists(accessToken)
      for (const playlist of playlists) {
        await db.runAsync(
          `INSERT OR IGNORE INTO playlists (id, user_id, name, description, track_count)
           VALUES (?, ?, ?, ?, ?)`,
          [playlist.id, userId, playlist.name, playlist.description, playlist.tracks.total]
        )
      }
      console.log(`Stored ${playlists.length} playlists`)
    } catch (playlistError) {
      console.error('Failed to fetch playlists:', playlistError.message)
    }

    console.log(`Successfully stored data for user ${userId}`)
  } catch (error) {
    console.error('Error fetching user data:', error)
  }
}

// Get user data
app.get('/api/user/:userId', async (req, res) => {
  try {
    const user = await db.getAsync(
      'SELECT id, spotify_id, display_name, email FROM users WHERE id = ?',
      [req.params.userId]
    )

    if (!user) {
      return res.status(404).json({ error: 'User not found' })
    }

    res.json(user)
  } catch (error) {
    console.error('Get user error:', error)
    res.status(500).json({ error: 'Failed to get user' })
  }
})

// Get user insights
app.get('/api/insights/:userId', async (req, res) => {
  try {
    const { userId } = req.params

    // Get stats
    const totalTracks = await db.getAsync(
      'SELECT COUNT(DISTINCT track_id) as count FROM user_tracks WHERE user_id = ?',
      [userId]
    )

    const totalArtists = await db.getAsync(
      'SELECT COUNT(DISTINCT artist_id) as count FROM user_artists WHERE user_id = ?',
      [userId]
    )

    const totalPlaylists = await db.getAsync(
      'SELECT COUNT(*) as count FROM playlists WHERE user_id = ?',
      [userId]
    )

    // Get audio features for user's tracks
    const audioFeatures = await db.allAsync(`
      SELECT af.* FROM audio_features af
      JOIN user_tracks ut ON af.track_id = ut.track_id
      WHERE ut.user_id = ?
    `, [userId])

    if (audioFeatures.length === 0) {
      return res.json({ message: 'No data available yet' })
    }

    // Calculate averages
    const avgFeatures = {
      danceability: 0,
      energy: 0,
      speechiness: 0,
      acousticness: 0,
      instrumentalness: 0,
      valence: 0
    }

    audioFeatures.forEach(f => {
      avgFeatures.danceability += f.danceability
      avgFeatures.energy += f.energy
      avgFeatures.speechiness += f.speechiness
      avgFeatures.acousticness += f.acousticness
      avgFeatures.instrumentalness += f.instrumentalness
      avgFeatures.valence += f.valence
    })

    Object.keys(avgFeatures).forEach(key => {
      avgFeatures[key] /= audioFeatures.length
    })

    // Prepare radar chart data
    const radarData = [
      { feature: 'danceability', value: avgFeatures.danceability },
      { feature: 'energy', value: avgFeatures.energy },
      { feature: 'speechiness', value: avgFeatures.speechiness },
      { feature: 'acousticness', value: avgFeatures.acousticness },
      { feature: 'instrumentalness', value: avgFeatures.instrumentalness },
      { feature: 'valence', value: avgFeatures.valence }
    ]

    // Generate mood progression (simulated 6 months)
    const months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun']
    const moodProgression = months.map((month, index) => {
      // Simulate variation over time
      const variation = (Math.sin(index) + 1) / 2
      return {
        month,
        valence: avgFeatures.valence * (0.8 + variation * 0.4),
        energy: avgFeatures.energy * (0.8 + variation * 0.4)
      }
    })

    // Get top artists
    const topArtists = await db.allAsync(`
      SELECT a.name, COUNT(*) as count
      FROM artists a
      JOIN user_artists ua ON a.id = ua.artist_id
      WHERE ua.user_id = ?
      GROUP BY a.id
      ORDER BY count DESC
      LIMIT 10
    `, [userId])

    // Get genre distribution
    const artistsWithGenres = await db.allAsync(`
      SELECT a.genres
      FROM artists a
      JOIN user_artists ua ON a.id = ua.artist_id
      WHERE ua.user_id = ?
    `, [userId])

    const genreCounts = {}
    artistsWithGenres.forEach(row => {
      try {
        const genres = JSON.parse(row.genres)
        genres.forEach(genre => {
          genreCounts[genre] = (genreCounts[genre] || 0) + 1
        })
      } catch (e) {}
    })

    const genres = Object.entries(genreCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([genre, count]) => ({ genre, count }))

    // Prepare scatter data
    const scatterData = audioFeatures
      .slice(0, 50)
      .map(f => ({
        energy: f.energy,
        valence: f.valence,
        danceability: f.danceability
      }))

    res.json({
      stats: {
        totalTracks: totalTracks.count,
        totalArtists: totalArtists.count,
        totalPlaylists: totalPlaylists.count
      },
      audioFeatures: radarData,
      moodProgression,
      topArtists,
      genres,
      scatterData
    })
  } catch (error) {
    console.error('Get insights error:', error)
    res.status(500).json({ error: 'Failed to get insights' })
  }
})

// Party routes
app.post('/api/parties', async (req, res) => {
  try {
    const { name, creatorId } = req.body
    const partyId = crypto.randomUUID()

    await db.runAsync(
      'INSERT INTO parties (id, name, creator_id) VALUES (?, ?, ?)',
      [partyId, name, creatorId]
    )

    // Add creator as first member
    await db.runAsync(
      'INSERT INTO party_members (party_id, user_id) VALUES (?, ?)',
      [partyId, creatorId]
    )

    res.json({ id: partyId, name, creator_id: creatorId })
  } catch (error) {
    console.error('Create party error:', error)
    res.status(500).json({ error: 'Failed to create party' })
  }
})

app.get('/api/parties/user/:userId', async (req, res) => {
  try {
    const parties = await db.allAsync(`
      SELECT p.*,
             COUNT(DISTINCT pm.user_id) as member_count,
             CASE WHEN pm_user.user_id IS NOT NULL THEN 1 ELSE 0 END as is_member
      FROM parties p
      LEFT JOIN party_members pm ON p.id = pm.party_id
      LEFT JOIN party_members pm_user ON p.id = pm_user.party_id AND pm_user.user_id = ?
      GROUP BY p.id
      ORDER BY p.created_at DESC
    `, [req.params.userId])

    res.json(parties)
  } catch (error) {
    console.error('Get parties error:', error)
    res.status(500).json({ error: 'Failed to get parties' })
  }
})

app.post('/api/parties/:partyId/join', async (req, res) => {
  try {
    const { partyId } = req.params
    const { userId } = req.body

    // Check if already a member
    const existing = await db.getAsync(
      'SELECT * FROM party_members WHERE party_id = ? AND user_id = ?',
      [partyId, userId]
    )

    if (!existing) {
      await db.runAsync(
        'INSERT INTO party_members (party_id, user_id) VALUES (?, ?)',
        [partyId, userId]
      )
    }

    res.json({ success: true })
  } catch (error) {
    console.error('Join party error:', error)
    res.status(500).json({ error: 'Failed to join party' })
  }
})

app.get('/api/parties/:partyId/insights', async (req, res) => {
  try {
    const { partyId } = req.params

    // Get party members
    const members = await db.allAsync(`
      SELECT u.id, u.display_name
      FROM users u
      JOIN party_members pm ON u.id = pm.user_id
      WHERE pm.party_id = ?
    `, [partyId])

    if (members.length === 0) {
      return res.json({ message: 'No members in party' })
    }

    // Get audio features for each member
    const memberFeatures = {}
    for (const member of members) {
      const features = await db.allAsync(`
        SELECT af.* FROM audio_features af
        JOIN user_tracks ut ON af.track_id = ut.track_id
        WHERE ut.user_id = ?
      `, [member.id])

      if (features.length > 0) {
        const avg = {
          danceability: 0,
          energy: 0,
          speechiness: 0,
          acousticness: 0,
          instrumentalness: 0,
          valence: 0
        }

        features.forEach(f => {
          avg.danceability += f.danceability
          avg.energy += f.energy
          avg.speechiness += f.speechiness
          avg.acousticness += f.acousticness
          avg.instrumentalness += f.instrumentalness
          avg.valence += f.valence
        })

        Object.keys(avg).forEach(key => {
          avg[key] /= features.length
        })

        memberFeatures[member.id] = avg
      }
    }

    // Create radar data
    const radarData = [
      { feature: 'danceability' },
      { feature: 'energy' },
      { feature: 'speechiness' },
      { feature: 'acousticness' },
      { feature: 'instrumentalness' },
      { feature: 'valence' }
    ]

    radarData.forEach(item => {
      members.forEach(member => {
        if (memberFeatures[member.id]) {
          item[`user_${member.id}`] = memberFeatures[member.id][item.feature]
        }
      })
    })

    // Create mood alignment over time
    const months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun']
    const moodAlignment = months.map((month, index) => {
      const dataPoint = { month }
      const variation = (Math.sin(index) + 1) / 2

      members.forEach(member => {
        if (memberFeatures[member.id]) {
          dataPoint[`user_${member.id}`] = memberFeatures[member.id].valence * (0.8 + variation * 0.4)
        }
      })

      return dataPoint
    })

    // Find common artists
    const commonArtists = await db.allAsync(`
      SELECT a.name, COUNT(DISTINCT ua.user_id) as shared_by
      FROM artists a
      JOIN user_artists ua ON a.id = ua.artist_id
      JOIN party_members pm ON ua.user_id = pm.user_id
      WHERE pm.party_id = ?
      GROUP BY a.id
      HAVING COUNT(DISTINCT ua.user_id) > 1
      ORDER BY shared_by DESC
      LIMIT 10
    `, [partyId])

    // Calculate compatibility (average valence similarity)
    let compatibility = 1
    if (members.length > 1) {
      const valences = members.map(m => memberFeatures[m.id]?.valence || 0.5)
      const avgValence = valences.reduce((a, b) => a + b, 0) / valences.length
      const variance = valences.reduce((sum, v) => sum + Math.pow(v - avgValence, 2), 0) / valences.length
      compatibility = Math.max(0, 1 - variance * 2)
    }

    res.json({
      members,
      radarData,
      moodAlignment,
      commonArtists,
      compatibility
    })
  } catch (error) {
    console.error('Get party insights error:', error)
    res.status(500).json({ error: 'Failed to get party insights' })
  }
})

app.listen(PORT, () => {
  console.log(`Audire backend running on http://localhost:${PORT}`)
})
