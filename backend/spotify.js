import axios from 'axios'
import dotenv from 'dotenv'

dotenv.config()

const SPOTIFY_API_BASE = 'https://api.spotify.com/v1'
const SPOTIFY_ACCOUNTS_BASE = 'https://accounts.spotify.com'

export function getAuthorizationUrl() {
  const scopes = [
    'user-read-private',
    'user-read-email',
    'user-top-read',
    'user-read-recently-played',
    'playlist-read-private',
    'playlist-read-collaborative'
  ]

  const params = new URLSearchParams({
    client_id: process.env.SPOTIFY_CLIENT_ID,
    response_type: 'code',
    redirect_uri: process.env.SPOTIFY_REDIRECT_URI,
    scope: scopes.join(' ')
  })

  return `${SPOTIFY_ACCOUNTS_BASE}/authorize?${params.toString()}`
}

export async function exchangeCodeForToken(code) {
  const response = await axios.post(
    `${SPOTIFY_ACCOUNTS_BASE}/api/token`,
    new URLSearchParams({
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: process.env.SPOTIFY_REDIRECT_URI
    }),
    {
      headers: {
        'Authorization': 'Basic ' + Buffer.from(
          process.env.SPOTIFY_CLIENT_ID + ':' + process.env.SPOTIFY_CLIENT_SECRET
        ).toString('base64'),
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    }
  )

  return response.data
}

export async function getUserProfile(accessToken) {
  const response = await axios.get(`${SPOTIFY_API_BASE}/me`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  })
  return response.data
}

export async function getTopTracks(accessToken, timeRange = 'medium_term', limit = 50) {
  const response = await axios.get(`${SPOTIFY_API_BASE}/me/top/tracks`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
    params: { time_range: timeRange, limit }
  })
  return response.data.items
}

export async function getTopArtists(accessToken, timeRange = 'medium_term', limit = 50) {
  const response = await axios.get(`${SPOTIFY_API_BASE}/me/top/artists`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
    params: { time_range: timeRange, limit }
  })
  return response.data.items
}

export async function getRecentlyPlayed(accessToken, limit = 50) {
  const response = await axios.get(`${SPOTIFY_API_BASE}/me/player/recently-played`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
    params: { limit }
  })
  return response.data.items
}

export async function getUserPlaylists(accessToken) {
  const response = await axios.get(`${SPOTIFY_API_BASE}/me/playlists`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
    params: { limit: 50 }
  })
  return response.data.items
}

export async function getAudioFeatures(accessToken, trackIds) {
  // Spotify API accepts max 100 IDs at once
  const chunks = []
  for (let i = 0; i < trackIds.length; i += 100) {
    chunks.push(trackIds.slice(i, i + 100))
  }

  const allFeatures = []
  for (const chunk of chunks) {
    const response = await axios.get(`${SPOTIFY_API_BASE}/audio-features`, {
      headers: { 'Authorization': `Bearer ${accessToken}` },
      params: { ids: chunk.join(',') }
    })
    allFeatures.push(...response.data.audio_features.filter(f => f !== null))
  }

  return allFeatures
}
