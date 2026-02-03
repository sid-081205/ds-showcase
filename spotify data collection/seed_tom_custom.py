
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
    conn.commit()
    conn.close()

def seed_tom_custom():
    # 1. Update Tom in master database with new email
    tom_spotify_id = "tomcrawdon_mock"
    tom_display_name = "Tom Crawdon"
    tom_email = "tomcrawdon" # Changed from tom@example.com
    
    print(f"Updating Tom in master database with email: {tom_email}")
    tom = master_db.add_user(
        spotify_user_id=tom_spotify_id,
        display_name=tom_display_name,
        email=tom_email,
        access_token="mock_token",
        refresh_token="mock_refresh",
        token_expiry=9999999999
    )
    
    tom_id = tom['id']
    tom_db_path = tom['db_path']
    
    # Reset/Create Tom's DB
    if os.path.exists(tom_db_path):
        os.remove(tom_db_path)
    setup_user_db(tom_db_path)
    
    conn = sqlite3.connect(tom_db_path)
    cursor = conn.cursor()

    # 2. Add Top Artists and Genres
    top_artists = [
        "JPEGMAFIA", "Kanye West", "JAY-Z", "Kendrick Lamar", "Drake", 
        "Travi$ Scott", "Lupe Fiasco", "Danny Brown", "Radiohead", "Denzel Curry"
    ]
    
    common_genres = [
        "Hip Hop", "Rap", "Experimental Hip Hop", "Indie Rock", "Art Rock", 
        "Pop", "R&B", "Alternative", "Soul", "Jazz Rap", "Neo-Soul", "Electronic"
    ]
    
    print("Inserting top artists and genres...")
    for idx, artist_name in enumerate(top_artists):
        # Assign some random genres from the common list
        artist_genres = random.sample(common_genres, 3)
        cursor.execute('''
            INSERT OR IGNORE INTO artists 
            (spotify_id, name, link, genres, popularity, followers, artist_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"art_{idx}", artist_name, f"https://open.spotify.com/artist/art_{idx}",
            ", ".join(artist_genres), random.randint(70, 99), random.randint(100000, 50000000), "top"
        ))

    # 3. Add Specific Songs from Images
    custom_songs = [
        # Image 1 & 3 combined
        {"name": "I'll Be Right There", "artist": "JPEGMAFIA", "album": "LAYOVER"},
        {"name": "either on or off the drugs", "artist": "JPEGMAFIA", "album": "LAYOVER"},
        {"name": "HAZARD DUTY PAY!", "artist": "JPEGMAFIA", "album": "LP!"},
        {"name": "DIKEMBE!", "artist": "JPEGMAFIA", "album": "LP!"},
        {"name": "Fentanyl Tester", "artist": "JPEGMAFIA", "album": "SCARING THE HOES"},
        {"name": "Easter Pink", "artist": "fakemink", "album": "Single"},
        {"name": "Phantom", "artist": "EsDeeKid", "album": "Single"},
        {"name": "Chains & Whips", "artist": "Clipse", "album": "Hell Hath No Fury"},
        {"name": "Poo-Putt Platter", "artist": "MF DOOM", "album": "MM...FOOD"},
        {"name": "Hurt Me Soul", "artist": "Lupe Fiasco", "album": "Food & Liquor"},
        {"name": "Touch (feat. Paul Williams)", "artist": "Daft Punk, Paul Williams", "album": "Random Access Memories"},
        {"name": "ANTI-HERO", "artist": "Ghais Guevara", "album": "There Will Be No Super-Slave"},
        {"name": "Fever", "artist": "Buckshot, fakemink", "album": "Single"},
        {"name": "Alright - 2015 Remaster", "artist": "Supergrass", "album": "I Should Coco"},
        {"name": "All In", "artist": "Earl Sweatshirt, LUCKI", "album": "Single"},
        {"name": "Sunday (feat. Frank Ocean)", "artist": "Earl Sweatshirt, Frank Ocean", "album": "Doris"},
        {"name": "Fire in the Hole", "artist": "Earl Sweatshirt", "album": "SICK!"},
        {"name": "Loving Machine", "artist": "TV Girl", "album": "French Exit"}
    ]

    print("Inserting custom tracks...")
    for idx, song in enumerate(custom_songs):
        spotify_id = f"custom_{idx}"
        # Random mood values for these custom ones
        moods = {
            "danceability": random.uniform(0.4, 0.9),
            "mood_happy": random.uniform(0.2, 0.8),
            "mood_sad": random.uniform(0.1, 0.6),
            "mood_aggressive": random.uniform(0.3, 0.9),
            "mood_relaxed": random.uniform(0.1, 0.5)
        }
        
        for table in ['top_tracks', 'recent_tracks']:
            cursor.execute(f'''
                INSERT OR IGNORE INTO {table} 
                (spotify_id, name, artist, album, link, danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                spotify_id, song['name'], song['artist'], song['album'], 
                f"https://open.spotify.com/track/{spotify_id}",
                moods['danceability'], moods['mood_happy'], moods['mood_sad'], 
                moods['mood_aggressive'], moods['mood_relaxed']
            ))

    # 4. Fill the rest with Kaggle songs (up to 1000 total)
    print("Filling remaining tracks with Kaggle data...")
    kaggle_songs = []
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 1000 - len(custom_songs):
                break
            kaggle_songs.append(row)

    for song in kaggle_songs:
        spotify_id = song.get('track_id', f"kaggle_{random.randint(10000, 99999)}")
        name = song.get('name', 'Unknown')
        artist = song.get('artist', 'Unknown')
        album = "Kaggle Collection"
        
        # Audio features
        danceability = float(song.get('danceability', 0.5))
        energy = float(song.get('energy', 0.5))
        valence = float(song.get('valence', 0.5))
        acousticness = float(song.get('acousticness', 0.5))
        
        mood_happy = valence
        mood_sad = 1.0 - valence
        mood_aggressive = energy * (1.0 - valence)
        mood_relaxed = (1.0 - energy) * (1.0 - acousticness * 0.5)
        
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

    # 5. Add 20% top artists to the artists table
    # We want 20% of his tracks to be from "top artists"
    # Actually, the user said "add atleast 20% top artists". 
    # Let's add 200 artists as 'top' artists to the artists table.
    print("Adding 200 top artists from Kaggle...")
    unique_artists = list(set([song['artist'] for song in kaggle_songs]))
    random.shuffle(unique_artists)
    for i in range(min(200, len(unique_artists))):
        artist_name = unique_artists[i]
        artist_genres = random.sample(common_genres, 2)
        cursor.execute('''
            INSERT OR IGNORE INTO artists 
            (spotify_id, name, link, genres, popularity, followers, artist_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"kaggle_art_{i}", artist_name, f"https://open.spotify.com/artist/kaggle_art_{i}",
            ", ".join(artist_genres), random.randint(50, 95), random.randint(1000, 1000000), "top"
        ))

    conn.commit()
    conn.close()
    
    # 6. Mark as completed
    master_db.update_user_analysis_status(tom_id, 'completed', 100)
    print(f"✅ Tom has been customized and marked as completed!")

if __name__ == "__main__":
    seed_tom_custom()
