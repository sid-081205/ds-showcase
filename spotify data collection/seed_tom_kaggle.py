
import sqlite3
import os
import csv
import master_db
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), 'merged_data.csv')

def setup_user_db(db_path):
    """Initialize the schema for a user's personal database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Recent Tracks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recent_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT UNIQUE,
            name TEXT,
            artist TEXT,
            album TEXT,
            isrc TEXT,
            link TEXT,
            danceability REAL,
            mood_happy REAL,
            mood_sad REAL,
            mood_aggressive REAL,
            mood_relaxed REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Top Tracks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS top_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT UNIQUE,
            name TEXT,
            artist TEXT,
            album TEXT,
            isrc TEXT,
            link TEXT,
            danceability REAL,
            mood_happy REAL,
            mood_sad REAL,
            mood_aggressive REAL,
            mood_relaxed REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Artists table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT,
            name TEXT,
            link TEXT,
            genres TEXT,
            popularity INTEGER,
            followers INTEGER,
            image_url TEXT,
            artist_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(spotify_id, artist_type)
        )
    ''')
    
    # Playlists table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT UNIQUE,
            name TEXT,
            link TEXT,
            owner TEXT,
            total_tracks INTEGER,
            image_url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Episodes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT UNIQUE,
            name TEXT,
            description TEXT,
            show_name TEXT,
            link TEXT,
            duration_ms INTEGER,
            release_date TEXT,
            image_url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def seed_tom_kaggle():
    print(f"Reading songs from {CSV_PATH}...")
    songs = []
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 1000:
                    break
                songs.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Found {len(songs)} songs.")

    # 1. Add/Update Tom in master database
    tom_spotify_id = "tomcrawdon_mock"
    tom_display_name = "Tom Crawdon"
    tom_email = "tom@example.com"
    
    tom = master_db.get_user_by_spotify_id(tom_spotify_id)
    if not tom:
        print("Creating mock user Tom...")
        tom = master_db.add_user(
            spotify_user_id=tom_spotify_id,
            display_name=tom_display_name,
            email=tom_email,
            access_token="mock_token",
            refresh_token="mock_refresh",
            token_expiry=9999999999
        )
    else:
        print("Tom already exists, updating data...")
    
    tom_id = tom['id']
    tom_db_path = tom['db_path']
    
    # Reset/Create Tom's DB
    if os.path.exists(tom_db_path):
        os.remove(tom_db_path)
    setup_user_db(tom_db_path)
    
    # 2. Populate Tom's data
    conn = sqlite3.connect(tom_db_path)
    cursor = conn.cursor()
    
    print("Inserting songs into Tom's database...")
    for song in songs:
        # Map values
        spotify_id = song.get('track_id', f"mock_{random.randint(1000, 9999)}")
        name = song.get('name', 'Unknown')
        artist = song.get('artist', 'Unknown')
        album = "Kaggle Collection"
        danceability = float(song.get('danceability', 0.5))
        energy = float(song.get('energy', 0.5))
        valence = float(song.get('valence', 0.5))
        acousticness = float(song.get('acousticness', 0.5))
        
        # Simple mood mapping logic
        mood_happy = valence
        mood_sad = 1.0 - valence
        mood_aggressive = energy * (1.0 - valence) # High energy, low valence = aggressive
        mood_relaxed = (1.0 - energy) * (1.0 - acousticness * 0.5) # Low energy = relaxed
        
        # Ensure values are within [0, 1]
        mood_happy = min(1.0, max(0.0, mood_happy))
        mood_sad = min(1.0, max(0.0, mood_sad))
        mood_aggressive = min(1.0, max(0.0, mood_aggressive))
        mood_relaxed = min(1.0, max(0.0, mood_relaxed))

        # Insert into both tables
        for table in ['top_tracks', 'recent_tracks']:
            cursor.execute(f'''
                INSERT OR IGNORE INTO {table} 
                (spotify_id, name, artist, album, link, danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                spotify_id, name, artist, album, 
                f"https://open.spotify.com/track/{spotify_id}",
                danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed
            ))
            
    conn.commit()
    conn.close()
    
    # 3. Mark as completed
    master_db.update_user_analysis_status(tom_id, 'completed', 100)
    print(f"✅ Tom has been seeded with {len(songs)} songs from Kaggle and marked as completed!")

if __name__ == "__main__":
    seed_tom_kaggle()
