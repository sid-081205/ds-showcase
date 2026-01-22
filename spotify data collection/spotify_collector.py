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
scope = "user-top-read,user-read-recently-played"

app = Flask(__name__)
CORS(app)

# Global progress state
progress_state = {
    "is_running": False,
    "progress": 0,
    "total": 0,
    "current_track": "",
    "status": "idle"
}

# Initialize SpotifyOAuth
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

print(f"--- DEBUG CONFIG ---")
print(f"ID: {client_id[:5]}...")
print(f"URI: {redirect_uri}")
print(f"--------------------")

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def save_track(conn, track_data, track_type):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM tracks WHERE isrc = ? AND track_type = ?', (track_data['isrc'], track_type))
    if cursor.fetchone():
        return

    cursor.execute('''
        INSERT INTO tracks (name, artist, album, isrc, link, danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed, track_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        track_data['name'],
        track_data['artist'],
        track_data['album'],
        track_data['isrc'],
        track_data['link'],
        track_data.get('danceability'),
        track_data.get('mood_happy'),
        track_data.get('mood_sad'),
        track_data.get('mood_aggressive'),
        track_data.get('mood_relaxed'),
        track_type
    ))
    conn.commit()

session = requests.Session()
session.headers.update({'User-Agent': 'MyMusicApp/1.0'})

def get_mbid_by_isrc(isrc):
    url = f"https://musicbrainz.org/ws/2/isrc/{isrc}"
    try:
        response = requests.get(url, params={'fmt': 'json'}, headers=session.headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('recordings'):
                return data['recordings'][0]['id']
    except:
        pass
    return None

def get_acoustic_features(mbid):
    url = f"https://acousticbrainz.org/api/v1/{mbid}/high-level"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'danceability': data['highlevel']['danceability']['all']['danceable'],
                'mood_happy': data['highlevel']['mood_happy']['all']['happy'],
                'mood_sad': data['highlevel']['mood_sad']['all']['sad'],
                'mood_aggressive': data['highlevel']['mood_aggressive']['all']['aggressive'],
                'mood_relaxed': data['highlevel']['mood_relaxed']['all']['relaxed'],
            }
    except:
        pass
    return None

def process_tracks(tracks, track_type, conn, start_offset=0, total_overall=0):
    for i, track in enumerate(tracks):
        current_idx = start_offset + i + 1
        progress_state["current_track"] = f"{track['name']} - {track['artist']}"
        progress_state["progress"] = int((current_idx / total_overall) * 100)
        
        mbid = get_mbid_by_isrc(track['isrc'])
        time.sleep(1.0) # Respect rate limits
        
        if mbid:
            features = get_acoustic_features(mbid)
            time.sleep(1.0)
            if features:
                track.update(features)
                save_track(conn, track, track_type)
        
        if i == 56: # Original script limit
            break

def collection_task(token_info):
    global progress_state
    progress_state["is_running"] = True
    progress_state["status"] = "Fetching Tracks"
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    conn = setup_db()
    
    # 1. Recent Tracks
    results_recent = sp.current_user_recently_played(limit=50)
    recent_tracks = []
    if results_recent and 'items' in results_recent:
        for item in results_recent['items']:
            track = item['track']
            recent_tracks.append({
                'name': track['name'],
                'link': track['external_urls']['spotify'],
                'isrc': track['external_ids']['isrc'],
                'album': track['album']['name'],
                'artist': track['artists'][0]['name']
            })
            
    # 2. Top Tracks
    all_top_tracks = []
    results = sp.current_user_top_tracks(limit=50, time_range="short_term")
    if results and 'items' in results:
        for item in results['items']:
            all_top_tracks.append({
                'name': item['name'],
                'link': item['external_urls']['spotify'],
                'isrc': item['external_ids']['isrc'],
                'album': item['album']['name'],
                'artist': item['artists'][0]['name']
            })
            
    total_tracks = len(recent_tracks) + len(all_top_tracks)
    progress_state["total"] = total_tracks
    progress_state["status"] = "Analyzing DNA"
    
    process_tracks(recent_tracks, 'recent', conn, 0, total_tracks)
    process_tracks(all_top_tracks, 'top', conn, len(recent_tracks), total_tracks)
    
    conn.close()
    progress_state["is_running"] = False
    progress_state["progress"] = 100
    progress_state["status"] = "Complete"
    progress_state["current_track"] = ""

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
    return jsonify(progress_state)

if __name__ == "__main__":
    app.run(port=8888)
