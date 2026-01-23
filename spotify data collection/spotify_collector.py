import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
import sqlite3
import os
import threading
from flask import Flask, redirect, request, jsonify
from flask_cors import CORS

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

# Initialize SpotifyOAuth
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope, 
    cache_path=".cache"
)

def setup_db():
    db_path = os.path.join(os.path.dirname(__file__), 'spotify_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tracks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT,
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
            track_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(spotify_id, track_type)
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

def save_track(conn, track_data, track_type):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO tracks 
        (spotify_id, name, artist, album, isrc, link, track_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        track_data['spotify_id'],
        track_data['name'],
        track_data['artist'],
        track_data['album'],
        track_data.get('isrc'),
        track_data['link'],
        track_type
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
    
    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Store user info
        user = sp.current_user()
        progress_state["user_info"] = {
            "display_name": user.get("display_name"),
            "id": user.get("id"),
            "image": user.get("images")[0]["url"] if user.get("images") else None
        }
        
        conn = setup_db()
        
        # 1. Recent Tracks
        progress_state["status"] = "Fetching Recent Tracks"
        results_recent = sp.current_user_recently_played(limit=50)
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
                }, 'recent')
        progress_state["progress"] = 15
                
        # 2. Top Tracks
        progress_state["status"] = "Fetching Top Tracks"
        results_top = sp.current_user_top_tracks(limit=50, time_range="short_term")
        if results_top and 'items' in results_top:
            for item in results_top['items']:
                save_track(conn, {
                    'spotify_id': item['id'],
                    'name': item['name'],
                    'link': item['external_urls']['spotify'],
                    'isrc': item.get('external_ids', {}).get('isrc'),
                    'album': item['album']['name'],
                    'artist': item['artists'][0]['name']
                }, 'top')
        progress_state["progress"] = 30

        # 3. Followed Artists
        progress_state["status"] = "Fetching Followed Artists"
        results_followed = sp.current_user_followed_artists(limit=50)
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
        progress_state["progress"] = 45

        # 4. Top Artists
        progress_state["status"] = "Fetching Top Artists"
        results_top_artists = sp.current_user_top_artists(limit=50, time_range="medium_term")
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
        progress_state["progress"] = 60

        # 5. Playlists
        progress_state["status"] = "Fetching Playlists"
        results_playlists = sp.current_user_playlists(limit=50)
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
        progress_state["progress"] = 80

        # 6. Saved Episodes
        progress_state["status"] = "Fetching Saved Episodes"
        try:
            results_episodes = sp.current_user_saved_episodes(limit=50)
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
        except Exception as e:
            print(f"Error fetching episodes: {e}")
            
        progress_state["progress"] = 100
        progress_state["status"] = "Complete"
        conn.close()
    except Exception as e:
        print(f"Collection task failed: {e}")
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

@app.route('/status')
def status():
    # If not running but we have a cache, try to get user info if missing
    if not progress_state["is_running"] and not progress_state["user_info"]:
        token_info = sp_oauth.get_cached_token()
        if token_info:
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
    return jsonify(progress_state)

@app.route('/logout', methods=['POST'])
def logout():
    global progress_state
    
    # First, let's try to clear the global oauth object's cache
    try:
        if os.path.exists(".cache"):
            os.remove(".cache")
    except Exception as e:
        print(f"Error removing .cache: {e}")
    
    # Clear database
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'spotify_data.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tracks")
            cursor.execute("DELETE FROM artists")
            cursor.execute("DELETE FROM playlists")
            cursor.execute("DELETE FROM episodes")
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Error clearing database: {e}")
    
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
