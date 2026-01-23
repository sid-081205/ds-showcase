import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
import sqlite3
import os
import threading
from flask import Flask, redirect, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configuration
# Ensure the following environment variables are set:
# SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
scope = "user-top-read,user-read-recently-played,user-follow-read,playlist-read-private,playlist-read-collaborative,user-library-read"

app = Flask(__name__)
CORS(app)

# Global progress state
progress_state = {
    "is_running": False,
    "progress": 0,
    "total": 6,  # 6 categories of data
    "current_track": "",
    "status": "idle",
    "user_info": None
}

# Determine absolute paths for consistency
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(BASE_DIR, ".cache")
DB_PATH = os.path.join(BASE_DIR, "spotify_data.db")

# Initialize SpotifyOAuth
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope, 
    cache_path=CACHE_PATH,
    show_dialog=True
)

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop deprecated tracks table if it exists
    cursor.execute('DROP TABLE IF EXISTS tracks')
    
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
    return conn

def save_track(conn, track_data, table_name):
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT OR IGNORE INTO {table_name} 
        (spotify_id, name, artist, album, isrc, link)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        track_data['spotify_id'],
        track_data['name'],
        track_data['artist'],
        track_data['album'],
        track_data.get('isrc'),
        track_data['link']
    ))
    conn.commit()

def save_artist(conn, artist_data, artist_type):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO artists 
        (spotify_id, name, link, genres, popularity, followers, image_url, artist_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        artist_data['spotify_id'],
        artist_data['name'],
        artist_data['link'],
        artist_data['genres'],
        artist_data['popularity'],
        artist_data['followers'],
        artist_data.get('image_url'),
        artist_type
    ))
    conn.commit()

def save_playlist(conn, playlist_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO playlists 
        (spotify_id, name, link, owner, total_tracks, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        playlist_data['spotify_id'],
        playlist_data['name'],
        playlist_data['link'],
        playlist_data['owner'],
        playlist_data['total_tracks'],
        playlist_data.get('image_url')
    ))
    conn.commit()

def save_episode(conn, episode_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO episodes 
        (spotify_id, name, description, show_name, link, duration_ms, release_date, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        episode_data['spotify_id'],
        episode_data['name'],
        episode_data['description'],
        episode_data['show_name'],
        episode_data['link'],
        episode_data['duration_ms'],
        episode_data.get('release_date'),
        episode_data.get('image_url')
    ))
    conn.commit()

def collection_task(token_info):
    global progress_state
    progress_state["is_running"] = True
    progress_state["progress"] = 0
    progress_state["status"] = "Initialising"
    
    print("🚀 Starting background collection task...")
    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Store user info
        user = sp.current_user()
        print(f"👤 Logged in as: {user.get('display_name')} ({user.get('id')})")
        progress_state["user_info"] = {
            "display_name": user.get("display_name"),
            "id": user.get("id"),
            "image": user.get("images")[0]["url"] if user.get("images") else None
        }
        
        conn = setup_db()
        
        # 1. Recent Tracks
        progress_state["status"] = "Fetching Recent Tracks"
        print("🎵 Fetching recent tracks...")
        results_recent = sp.current_user_recently_played(limit=50)
        saved_recent = 0
        if results_recent and 'items' in results_recent:
            for item in results_recent['items']:
                track = item['track']
                save_track(conn, {
                    'spotify_id': track['id'],
                    'name': track['name'],
                    'link': track['external_urls']['spotify'],
                    'isrc': track.get('external_ids', {}).get('isrc'),
                    'album': track['album']['name'],
                    'artist': track['artists'][0]['name']
                }, 'recent_tracks')
                saved_recent += 1
        print(f"✅ Saved {saved_recent} recent tracks.")
        progress_state["progress"] = 15
                
        # 2. Top Tracks - Paginated with Progress Update
        progress_state["status"] = "Fetching Top Tracks"
        print("🔝 Fetching top tracks...")
        offset = 0
        limit = 50
        fetched_count = 0
        
        # Get total to calculate progress
        initial_results = sp.current_user_top_tracks(limit=1, offset=0)
        total_top_tracks = initial_results.get('total', 50) 
        
        while True:
            results_top = sp.current_user_top_tracks(limit=limit, offset=offset)
            if not results_top or not results_top['items']:
                break
                
            for item in results_top['items']:
                save_track(conn, {
                    'spotify_id': item['id'],
                    'name': item['name'],
                    'link': item['external_urls']['spotify'],
                    'isrc': item.get('external_ids', {}).get('isrc'),
                    'album': item['album']['name'],
                    'artist': item['artists'][0]['name']
                }, 'top_tracks')
                fetched_count += 1
                
                granular_progress = 15 + (fetched_count / total_top_tracks * 15)
                progress_state["progress"] = min(30, int(granular_progress))
            
            offset += limit
            if len(results_top['items']) < limit:
                break
        print(f"✅ Total top tracks saved: {fetched_count}")
        progress_state["progress"] = 30
 
        # 3. Followed Artists
        progress_state["status"] = "Fetching Followed Artists"
        print("👥 Fetching followed artists...")
        results_followed = sp.current_user_followed_artists(limit=50)
        saved_followed = 0
        if results_followed and 'artists' in results_followed:
            for artist in results_followed['artists']['items']:
                save_artist(conn, {
                    'spotify_id': artist['id'],
                    'name': artist['name'],
                    'link': artist['external_urls']['spotify'],
                    'genres': ",".join(artist['genres']),
                    'popularity': artist['popularity'],
                    'followers': artist['followers']['total'],
                    'image_url': artist['images'][0]['url'] if artist['images'] else None
                }, 'followed')
                saved_followed += 1
        print(f"✅ Saved {saved_followed} followed artists.")
        progress_state["progress"] = 45
 
        # 4. Top Artists (Non-paginated as per request)
        progress_state["status"] = "Fetching Top Artists"
        print("🌟 Fetching top artists...")
        results_top_artists = sp.current_user_top_artists(limit=50)
        saved_top_artists = 0
        if results_top_artists and 'items' in results_top_artists:
            for artist in results_top_artists['items']:
                save_artist(conn, {
                    'spotify_id': artist['id'],
                    'name': artist['name'],
                    'link': artist['external_urls']['spotify'],
                    'genres': ",".join(artist['genres']),
                    'popularity': artist['popularity'],
                    'followers': artist['followers']['total'],
                    'image_url': artist['images'][0]['url'] if artist['images'] else None
                }, 'top')
                saved_top_artists += 1
        print(f"✅ Saved {saved_top_artists} top artists.")
        progress_state["progress"] = 60
 
        # 5. Playlists
        progress_state["status"] = "Fetching Playlists"
        print("📂 Fetching playlists...")
        results_playlists = sp.current_user_playlists(limit=50)
        saved_playlists = 0
        if results_playlists and 'items' in results_playlists:
            for playlist in results_playlists['items']:
                save_playlist(conn, {
                    'spotify_id': playlist['id'],
                    'name': playlist['name'],
                    'link': playlist['external_urls']['spotify'],
                    'owner': playlist['owner']['display_name'],
                    'total_tracks': playlist['tracks']['total'],
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None
                })
                saved_playlists += 1
        print(f"✅ Saved {saved_playlists} playlists.")
        progress_state["progress"] = 80
 
        # 6. Saved Episodes
        progress_state["status"] = "Fetching Saved Episodes"
        print("ℹ️ Fetching saved episodes...")
        try:
            results_episodes = sp.current_user_saved_episodes(limit=50)
            saved_episodes = 0
            if results_episodes and 'items' in results_episodes:
                for item in results_episodes['items']:
                    episode = item['episode']
                    save_episode(conn, {
                        'spotify_id': episode['id'],
                        'name': episode['name'],
                        'description': episode['description'],
                        'show_name': episode['show']['name'],
                        'link': episode['external_urls']['spotify'],
                        'duration_ms': episode['duration_ms'],
                        'release_date': episode['release_date'],
                        'image_url': episode['images'][0]['url'] if episode['images'] else None
                    })
                    saved_episodes += 1
            print(f"✅ Saved {saved_episodes} episodes.")
        except Exception as e:
            print(f"❌ Error fetching episodes: {e}")
            
        progress_state["progress"] = 100
        progress_state["status"] = "Complete"
        print("🎉 Collection task completed successfully!")
        conn.close()
    except Exception as e:
        print(f"💥 Collection task failed: {e}")
        progress_state["status"] = f"Error: {e}"
    finally:
        progress_state["is_running"] = False

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return jsonify({"url": auth_url})

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    if token_info:
        # Start collection in background
        thread = threading.Thread(target=collection_task, args=(token_info,))
        thread.start()
        return "Authentication successful! You can close this window."
    return "Authentication failed.", 400

def clear_db():
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            tables = ['recent_tracks', 'top_tracks', 'artists', 'playlists', 'episodes']
            for table in tables:
                # Check if table exists before trying to delete
                cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone()[0] == 1:
                    cursor.execute(f"DELETE FROM {table}")
            cursor.execute("DROP TABLE IF EXISTS tracks")
            conn.commit()
            conn.close()
            print("Database cleared successfully.")
    except Exception as e:
        print(f"Error clearing database: {e}")

@app.route('/status')
def status():
    global progress_state
    token_info = sp_oauth.get_cached_token()
    
    # If we have a cache, try to get user info if missing
    if token_info:
        if not progress_state["is_running"] and not progress_state["user_info"]:
            try:
                # Use a fresh sp object for status check to avoid shared state issues
                temp_sp = spotipy.Spotify(auth=token_info['access_token'])
                user = temp_sp.current_user()
                progress_state["user_info"] = {
                    "display_name": user.get("display_name"),
                    "id": user.get("id"),
                    "image": user.get("images")[0]["url"] if user.get("images") else None
                }
            except:
                pass
    else:
        # Not connected - ensure database is empty as per requirement
        if not progress_state["is_running"]:
            clear_db()
            progress_state["user_info"] = None
            if progress_state["status"] == "Complete":
                progress_state["status"] = "idle"
                progress_state["progress"] = 0
            
    return jsonify(progress_state)

@app.route('/logout', methods=['POST'])
def logout():
    global progress_state
    
    # First, let's try to clear the global oauth object's cache using absolute path
    try:
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
            print(f"Cache cleared at {CACHE_PATH}")
    except Exception as e:
        print(f"Error removing cache: {e}")
    
    # Clear database
    clear_db()
    
    # Reset state
    progress_state = {
        "is_running": False,
        "progress": 0,
        "total": 6,
        "current_track": "",
        "status": "idle",
        "user_info": None
    }
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(port=8888)
