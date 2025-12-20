import sqlite3 from 'sqlite3'
import { promisify } from 'util'

const db = new sqlite3.Database('./audire.db')

// Promisify database methods
db.runAsync = promisify(db.run.bind(db))
db.getAsync = promisify(db.get.bind(db))
db.allAsync = promisify(db.all.bind(db))

// Initialize database schema
export async function initializeDatabase() {
  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      spotify_id TEXT UNIQUE,
      display_name TEXT,
      email TEXT,
      access_token TEXT,
      refresh_token TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS tracks (
      id TEXT PRIMARY KEY,
      name TEXT,
      artist TEXT,
      album TEXT,
      duration_ms INTEGER,
      popularity INTEGER
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS user_tracks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT,
      track_id TEXT,
      played_at DATETIME,
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (track_id) REFERENCES tracks(id)
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS audio_features (
      track_id TEXT PRIMARY KEY,
      danceability REAL,
      energy REAL,
      loudness REAL,
      speechiness REAL,
      acousticness REAL,
      instrumentalness REAL,
      liveness REAL,
      valence REAL,
      tempo REAL,
      FOREIGN KEY (track_id) REFERENCES tracks(id)
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS artists (
      id TEXT PRIMARY KEY,
      name TEXT,
      genres TEXT,
      popularity INTEGER
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS user_artists (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT,
      artist_id TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (artist_id) REFERENCES artists(id)
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS playlists (
      id TEXT PRIMARY KEY,
      user_id TEXT,
      name TEXT,
      description TEXT,
      track_count INTEGER,
      FOREIGN KEY (user_id) REFERENCES users(id)
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS parties (
      id TEXT PRIMARY KEY,
      name TEXT,
      creator_id TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (creator_id) REFERENCES users(id)
    )
  `)

  await db.runAsync(`
    CREATE TABLE IF NOT EXISTS party_members (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      party_id TEXT,
      user_id TEXT,
      joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (party_id) REFERENCES parties(id),
      FOREIGN KEY (user_id) REFERENCES users(id)
    )
  `)

  console.log('Database initialized successfully')
}

export default db
