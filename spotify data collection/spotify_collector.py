import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
import sqlite3
import os
import threading
from flask import Flask, redirect, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import master_db

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

# Global analyzer state
analyzer_state = {
    "is_running": False,
    "progress": 0,
    "total": 0,
    "analyzed": 0,
    "current_track": "",
    "status": "idle"
}

# Determine absolute paths for consistency
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(BASE_DIR, ".cache")
DB_PATH = os.path.join(BASE_DIR, "spotify_data.db")

from spotipy.cache_handler import MemoryCacheHandler

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
    # Pass 'main' as state to identify this flow in the callback
    auth_url = sp_oauth.get_authorize_url(state='main')
    return jsonify({"url": auth_url})

@app.route('/callback')
def callback():
    """Handle OAuth callback - supports main login and multi-user comparison"""
    print("🔍 CALLBACK ENDPOINT CALLED!")
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        print("   ❌ No code provided")
        return "Authentication failed: No code provided", 400
    
    try:
        # Determine if this is the main user or a comparison user
        is_main = (state == 'main')
        print(f"   ℹ️ Flow type: {'MAIN' if is_main else 'COMPARISON'} (state: {state})")
        
        if is_main:
            # Main flow: Updates the persistent .cache file
            token_info = sp_oauth.get_access_token(code)
        else:
            # Comparison flow: Use memory-only cache to avoid session leakage
            comp_oauth = SpotifyOAuth(
                client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
                scope=scope,
                cache_handler=MemoryCacheHandler()
            )
            token_info = comp_oauth.get_access_token(code)
            
        access_token = token_info['access_token']
        refresh_token = token_info['refresh_token']
        expires_at = token_info['expires_at']
        
        # Create Spotify client to identify the user
        sp = spotipy.Spotify(auth=access_token)
        user_info = sp.current_user()
        
        display_name = user_info['display_name']
        spotify_user_id = user_info['id']
        email = user_info.get('email', '')
        
        print(f"   👤 Authenticated as: {spotify_user_id} - {display_name}")
        
        # Add or update user in master database
        user = master_db.add_user(
            spotify_user_id=spotify_user_id,
            display_name=display_name,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expires_at
        )
        
        # Initialize their personal database
        setup_user_db(user['db_path'])
        
        # Start collection and analysis in background
        thread = threading.Thread(target=collect_and_analyze_task, args=(sp, user))
        thread.daemon = True
        thread.start()
        
        # Return success page
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <meta http-equiv="refresh" content="3;url=about:blank">
            <style>
                body {{ font-family: -apple-system, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #191414; color: white; }}
                .card {{ background: #282828; padding: 40px; border-radius: 20px; text-align: center; border: 2px solid #1DB954; max-width: 400px; }}
                .success {{ font-size: 48px; margin-bottom: 20px; }}
                h1 {{ color: #1DB954; font-size: 24px; margin: 10px 0; }}
                p {{ color: #b3b3b3; line-height: 1.6; }}
                .user-badge {{ background: #1DB954; color: black; padding: 5px 15px; border-radius: 20px; font-weight: bold; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="success">✅</div>
                <h1>Spotify Linked!</h1>
                <p>Authenticated as:</p>
                <div class="user-badge">{display_name}</div>
                <p>Data analysis has started. You can close this window and return to the app.</p>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f"   ❌ Error in callback: {e}")
        import traceback
        traceback.print_exc()
        return f"Authentication failed: {str(e)}", 500

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
    global progress_state, analyzer_state
    print("🧊 LOGOUT: Performing full system reset...")
    
    # 1. Clear Spotify Cache
    try:
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
            print(f"   ✅ Main cache cleared: {CACHE_PATH}")
    except Exception as e:
        print(f"   ❌ Error removing cache: {e}")
    
    # 2. Clear Main Database
    clear_db()
    
    # 3. Clear Master Users Database and User DBs
    try:
        users = master_db.get_all_users()
        for u in users:
            try:
                if 'db_path' in u and os.path.exists(u['db_path']):
                    os.remove(u['db_path'])
                    print(f"   ✅ Deleted user DB: {u['db_path']}")
            except Exception as e:
                print(f"   ⚠️ Could not delete user DB {u.get('db_path')}: {e}")
        
        # Truncate users table in master DB
        conn = sqlite3.connect(master_db.MASTER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        print("   ✅ Master users database cleared")
    except Exception as e:
        print(f"   ❌ Error clearing master DB: {e}")
    
    # 4. Reset Global States
    progress_state = {
        "is_running": False,
        "progress": 0,
        "total": 6,
        "current_track": "",
        "status": "idle",
        "user_info": None
    }
    
    analyzer_state = {
        "is_running": False,
        "progress": 0,
        "total": 0,
        "analyzed": 0,
        "current_track": "",
        "status": "idle",
        "output_lines": []
    }
    
    print("🏁 Logout complete!")
    return jsonify({"status": "success"})

def run_analyzer():
    """Run analyzer.py and track progress"""
    global analyzer_state
    import subprocess
    import re
    
    analyzer_state["is_running"] = True
    analyzer_state["status"] = "Initializing analyzer..."
    analyzer_state["progress"] = 0
    analyzer_state["output_lines"] = []  # Store recent output lines
    
    print("🔬 Starting analyzer.py...")
    
    def remove_emojis(text):
        """Remove emojis from text"""
        # Remove common emojis used in analyzer.py
        emoji_pattern = re.compile("["
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F700-\U0001F77F"  # alchemical symbols
            u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text).strip()
    
    try:
        # Get total tracks to analyze (only top_tracks now)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM top_tracks WHERE danceability IS NULL")
        total_tracks = cursor.fetchone()[0]
        analyzer_state["total"] = total_tracks
        conn.close()
        
        if total_tracks == 0:
            analyzer_state["status"] = "All tracks already analyzed"
            analyzer_state["progress"] = 100
            analyzer_state["is_running"] = False
            analyzer_state["output_lines"] = ["All tracks already analyzed"]
            return
        
        # Run analyzer.py with unbuffered output
        analyzer_path = os.path.join(BASE_DIR, "analyzer.py")
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
        
        process = subprocess.Popen(
            ["python3", "-u", analyzer_path],  # -u flag for unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        
        # Track progress by parsing output
        analyzed_count = 0
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            
            print(line.strip())  # Log to console
            
            # Clean and store output line (remove emojis)
            clean_line = remove_emojis(line.strip())
            if clean_line:  # Only add non-empty lines
                # Keep only the last 10 lines for display
                analyzer_state["output_lines"].append(clean_line)
                if len(analyzer_state["output_lines"]) > 10:
                    analyzer_state["output_lines"].pop(0)
            
            # Parse progress from output
            # Look for patterns like "[1/36] Analyzing: Track Name - Artist"
            match = re.search(r'\[(\d+)/(\d+)\] Analyzing: (.+?) - (.+)', line)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                track_name = match.group(3)
                artist_name = match.group(4)
                
                analyzer_state["current_track"] = f"{track_name} - {artist_name}"
                analyzer_state["progress"] = int((current / total_tracks) * 100)
                analyzer_state["analyzed"] = analyzed_count
            
            # Check for completion markers
            if "✅ Saved features for" in line or "Saved features for" in line:
                analyzed_count += 1
                analyzer_state["analyzed"] = analyzed_count
            
            # Check for table transitions
            if "Analyzing table: recent_tracks" in line:
                analyzer_state["status"] = "Analyzing recent tracks..."
            elif "Analyzing table: top_tracks" in line:
                analyzer_state["status"] = "Analyzing top tracks..."
        
        process.wait()
        
        if process.returncode == 0:
            analyzer_state["status"] = "Analysis complete!"
            analyzer_state["progress"] = 100
            print("✅ Analyzer completed successfully")
        else:
            analyzer_state["status"] = f"Analysis failed with code {process.returncode}"
            print(f"❌ Analyzer failed with return code {process.returncode}")
            
    except Exception as e:
        print(f"💥 Analyzer error: {e}")
        analyzer_state["status"] = f"Error: {str(e)}"
        analyzer_state["output_lines"] = [f"Error: {str(e)}"]
    finally:
        analyzer_state["is_running"] = False

@app.route('/analyze', methods=['POST'])
def analyze():
    """Start the analyzer in a background thread"""
    global analyzer_state
    
    if analyzer_state["is_running"]:
        return jsonify({"error": "Analyzer is already running"}), 400
    
    # Reset state
    analyzer_state = {
        "is_running": True,
        "progress": 0,
        "total": 0,
        "analyzed": 0,
        "current_track": "",
        "status": "Starting..."
    }
    
    # Run in background thread
    thread = threading.Thread(target=run_analyzer)
    thread.start()
    
    return jsonify({"status": "started"})

@app.route('/analyzer-status')
def analyzer_status():
    """Get current analyzer progress"""
    return jsonify(analyzer_state)

@app.route('/mood-data')
def get_mood_data():
    """Get comprehensive mood analysis data from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Check if we have any analyzed data
        cursor.execute("""
            SELECT COUNT(*) as count FROM top_tracks 
            WHERE danceability IS NOT NULL
        """)
        analyzed_count = cursor.fetchone()['count']
        
        if analyzed_count == 0:
            conn.close()
            return jsonify({"has_data": False})
        
        # Get top tracks with mood data
        cursor.execute("""
            SELECT name, artist, danceability, mood_happy, mood_sad, 
                   mood_aggressive, mood_relaxed
            FROM top_tracks 
            WHERE danceability IS NOT NULL
            ORDER BY id
            LIMIT 10
        """)
        top_tracks = [dict(row) for row in cursor.fetchall()]
        
        # Get top artists from top_tracks (most frequent artists)
        cursor.execute("""
            SELECT artist as name, COUNT(*) as track_count
            FROM top_tracks 
            WHERE danceability IS NOT NULL
            GROUP BY artist
            ORDER BY track_count DESC
            LIMIT 5
        """)
        top_artists_data = cursor.fetchall()
        
        # For each artist, try to get additional info from artists table if available
        top_artists = []
        for row in top_artists_data:
            artist_name = row['name']
            track_count = row['track_count']
            
            # Try to get artist details from artists table
            cursor.execute("""
                SELECT genres, popularity, followers, image_url
                FROM artists 
                WHERE name = ?
                LIMIT 1
            """, (artist_name,))
            artist_details = cursor.fetchone()
            
            if artist_details:
                top_artists.append({
                    'name': artist_name,
                    'genres': artist_details['genres'],
                    'popularity': artist_details['popularity'],
                    'followers': artist_details['followers'],
                    'image_url': artist_details['image_url']
                })
            else:
                # If not in artists table, use defaults
                top_artists.append({
                    'name': artist_name,
                    'genres': '',
                    'popularity': 50,  # Default popularity
                    'followers': 0,
                    'image_url': ''
                })
        
        # Calculate average mood scores
        cursor.execute("""
            SELECT 
                AVG(danceability) as avg_danceability,
                AVG(mood_happy) as avg_happy,
                AVG(mood_sad) as avg_sad,
                AVG(mood_aggressive) as avg_aggressive,
                AVG(mood_relaxed) as avg_relaxed
            FROM top_tracks
            WHERE danceability IS NOT NULL
        """)
        avg_moods = dict(cursor.fetchone())
        
        # Get recommended artists (different from top artists) from the artists table
        # Exclude the top artists we already found
        top_artist_names = [artist['name'] for artist in top_artists]
        placeholders = ','.join('?' * len(top_artist_names))
        
        cursor.execute(f"""
            SELECT name, genres, popularity, followers, image_url
            FROM artists 
            WHERE name NOT IN ({placeholders})
            AND popularity > 0
            ORDER BY popularity DESC
            LIMIT 5
        """, top_artist_names)
        recommended_artists = [dict(row) for row in cursor.fetchall()]
        
        # If we don't have enough recommended artists from the artists table,
        # get some from top_tracks that aren't in our top 5
        if len(recommended_artists) < 3:
            cursor.execute(f"""
                SELECT DISTINCT artist as name
                FROM top_tracks 
                WHERE danceability IS NOT NULL
                AND artist NOT IN ({placeholders})
                GROUP BY artist
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """, top_artist_names)
            
            for row in cursor.fetchall():
                if len(recommended_artists) >= 5:
                    break
                    
                artist_name = row['name']
                
                # Try to get details from artists table
                cursor.execute("""
                    SELECT genres, popularity, followers, image_url
                    FROM artists 
                    WHERE name = ?
                    LIMIT 1
                """, (artist_name,))
                artist_details = cursor.fetchone()
                
                if artist_details:
                    recommended_artists.append({
                        'name': artist_name,
                        'genres': artist_details['genres'],
                        'popularity': artist_details['popularity'],
                        'followers': artist_details['followers'],
                        'image_url': artist_details['image_url']
                    })
                else:
                    recommended_artists.append({
                        'name': artist_name,
                        'genres': '',
                        'popularity': 50,
                        'followers': 0,
                        'image_url': ''
                    })
        
        # Get genre distribution from top artists
        cursor.execute("""
            SELECT genres FROM artists WHERE artist_type = 'top' AND genres != ''
        """)
        genre_rows = cursor.fetchall()
        genre_counts = {}
        for row in genre_rows:
            genres = row['genres'].split(',')
            for genre in genres:
                genre = genre.strip()
                if genre:
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Get top 5 genres
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Count total tracks and artists
        cursor.execute("SELECT COUNT(*) as count FROM top_tracks")
        total_tracks = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT artist) as count FROM top_tracks")
        unique_artists = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            "has_data": True,
            "top_tracks": top_tracks,
            "top_artists": top_artists,
            "recommended_artists": recommended_artists,
            "average_moods": avg_moods,
            "top_genres": [{"name": g[0], "count": g[1]} for g in top_genres],
            "stats": {
                "total_tracks": total_tracks,
                "unique_artists": unique_artists,
                "analyzed_tracks": analyzed_count
            }
        })
        
    except Exception as e:
        print(f"Error fetching mood data: {e}")
        return jsonify({"error": str(e), "has_data": False}), 500

# ============================================================================
# MULTI-USER COMPARISON ENDPOINTS
# ============================================================================

@app.route('/add-user')
def add_user():
    """Initiate OAuth flow for adding a new user for comparison"""
    # Use MemoryCacheHandler to ensure we don't read from the main user's session
    comp_oauth = SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
        scope=scope,
        show_dialog=True,  # IMPORTANT: Forces the "Not you?" option
        cache_handler=MemoryCacheHandler()
    )
    # Use 'comparison' state to identify this flow in the callback
    auth_url = comp_oauth.get_authorize_url(state='comparison')
    return jsonify({"url": auth_url})

@app.route('/users')
def get_users():
    """Get all users and their analysis status, auto-importing main user if needed"""
    try:
        # Check if the "main" user is logged in and not in the master DB
        token_info = sp_oauth.get_cached_token()
        if token_info:
            sp = spotipy.Spotify(auth=token_info['access_token'])
            try:
                me = sp.current_user()
                # Check if this user is in master DB
                existing = master_db.get_user_by_spotify_id(me['id'])
                if not existing:
                    print(f"🔄 Auto-importing main user {me['display_name']} into comparison system")
                    user = master_db.add_user(
                        spotify_user_id=me['id'],
                        display_name=me['display_name'],
                        email=me.get('email', ''),
                        access_token=token_info['access_token'],
                        refresh_token=token_info.get('refresh_token', ''),
                        token_expiry=token_info['expires_at']
                    )
                    setup_user_db(user['db_path'])
                    # Trigger analysis in background
                    thread = threading.Thread(target=collect_and_analyze_task, args=(sp, user))
                    thread.daemon = True
                    thread.start()
            except Exception as me_err:
                print(f"⚠️ Error auto-importing main user: {me_err}")

        users = master_db.get_all_users()
        
        # Remove sensitive token information
        for user in users:
            user.pop('access_token', None)
            user.pop('refresh_token', None)
            user.pop('token_expiry', None)
        
        return jsonify({"users": users})
        
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({"error": str(e)}), 500

def collect_and_analyze_task(sp, user):
    """Background task to collect and then analyze user data"""
    try:
        user_id = user['id']
        db_path = user['db_path']
        
        # Update status
        master_db.update_user_analysis_status(user_id, 'running', 5)
        
        # 1. Collect Data
        print(f"📊 [User {user_id}] Starting data collection...")
        collect_all_data_for_user(sp, db_path, user_id)
        master_db.update_user_analysis_status(user_id, 'running', 40)
        
        # 2. Run Analyzer
        print(f"🔬 [User {user_id}] Starting mood analysis...")
        import subprocess
        analyzer_path = os.path.join(BASE_DIR, 'analyzer.py')
        
        process = subprocess.Popen(
            ["python3", analyzer_path, db_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                line_str = line.strip()
                print(f"[User {user_id}] {line_str}")
                # Try to parse progress if output contains it
                if "Processing" in line_str:
                    master_db.update_user_analysis_status(user_id, 'running', 60)
                elif "Analysis complete" in line_str:
                    master_db.update_user_analysis_status(user_id, 'running', 95)
        
        process.wait()
        
        if process.returncode == 0:
            print(f"✅ [User {user_id}] Analysis complete!")
            master_db.update_user_analysis_status(user_id, 'completed', 100)
        else:
            print(f"❌ [User {user_id}] Analyzer failed with code {process.returncode}")
            master_db.update_user_analysis_status(user_id, 'failed', 0)
            
    except Exception as e:
        print(f"❌ [User {user_id}] Error in background task: {e}")
        master_db.update_user_analysis_status(user['id'], 'failed', 0)

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user and their database"""
    try:
        success = master_db.delete_user(user_id)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "User not found"}), 404
            
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-user/<int:user_id>', methods=['POST'])
def analyze_user(user_id):
    """Trigger analyzer for a specific user"""
    try:
        user = master_db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user['analysis_status'] == 'running':
            return jsonify({"error": "Analysis already in progress"}), 400
        
        # Create Spotify client from stored tokens
        sp = spotipy.Spotify(auth=user['access_token'])
        
        # Run background task
        thread = threading.Thread(target=collect_and_analyze_task, args=(sp, user))
        thread.daemon = True
        thread.start()
        
        return jsonify({"success": True, "message": "Analysis started"})
        
    except Exception as e:
        print(f"Error in analyze_user: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/collect-user-data/<int:user_id>', methods=['POST'])
def collect_user_data(user_id):
    """Collect Spotify data for a specific user"""
    try:
        user = master_db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Create Spotify client with user's token
        sp = spotipy.Spotify(auth=user['access_token'])
        
        # Collect data using user's database
        def collect_data():
            try:
                collect_all_data_for_user(sp, user['db_path'], user_id)
            except Exception as e:
                print(f"Error collecting data for user {user_id}: {e}")
        
        thread = threading.Thread(target=collect_data)
        thread.daemon = True
        thread.start()
        
        return jsonify({"success": True, "message": "Data collection started"})
        
    except Exception as e:
        print(f"Error starting data collection: {e}")
        return jsonify({"error": str(e)}), 500

def setup_user_db(db_path):
    """Initialize database for a specific user"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the same tables as in setup_db()
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT UNIQUE,
            name TEXT,
            genres TEXT,
            popularity INTEGER,
            followers INTEGER,
            image_url TEXT,
            artist_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT UNIQUE,
            name TEXT,
            description TEXT,
            tracks_total INTEGER,
            owner TEXT,
            public BOOLEAN,
            collaborative BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_id TEXT UNIQUE,
            name TEXT,
            show_name TEXT,
            description TEXT,
            duration_ms INTEGER,
            release_date TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ User database initialized: {db_path}")

def collect_all_data_for_user(sp, db_path, user_id):
    """Collect all Spotify data for a specific user"""
    try:
        print(f"📊 Starting data collection for user {user_id}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Collect Top Tracks
        print(f"   🎵 Fetching top tracks...")
        try:
            top_tracks = sp.current_user_top_tracks(limit=50, time_range='medium_term')
            for track in top_tracks['items']:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO top_tracks 
                        (spotify_id, name, artist, album, isrc, link)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        track['id'],
                        track['name'],
                        track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        track['album']['name'],
                        track.get('external_ids', {}).get('isrc', ''),
                        track['external_urls'].get('spotify', '')
                    ))
                except Exception as e:
                    print(f"      ⚠️ Error saving track {track.get('name', 'Unknown')}: {e}")
            
            conn.commit()
            print(f"   ✅ Saved {len(top_tracks['items'])} top tracks")
        except Exception as e:
            print(f"   ❌ Error fetching top tracks: {e}")
        
        # 2. Collect Top Artists
        print(f"   🎤 Fetching top artists...")
        try:
            top_artists = sp.current_user_top_artists(limit=50, time_range='medium_term')
            for artist in top_artists['items']:
                try:
                    genres = ','.join(artist.get('genres', []))
                    image_url = artist['images'][0]['url'] if artist.get('images') else ''
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO artists 
                        (spotify_id, name, genres, popularity, followers, image_url, artist_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        artist['id'],
                        artist['name'],
                        genres,
                        artist.get('popularity', 0),
                        artist.get('followers', {}).get('total', 0),
                        image_url,
                        'top'
                    ))
                except Exception as e:
                    print(f"      ⚠️ Error saving artist {artist.get('name', 'Unknown')}: {e}")
            
            conn.commit()
            print(f"   ✅ Saved {len(top_artists['items'])} top artists")
        except Exception as e:
            print(f"   ❌ Error fetching top artists: {e}")
        
        # 3. Collect Recent Tracks
        print(f"   🕐 Fetching recently played tracks...")
        try:
            recent = sp.current_user_recently_played(limit=50)
            for item in recent['items']:
                track = item['track']
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO recent_tracks 
                        (spotify_id, name, artist, album, isrc, link)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        track['id'],
                        track['name'],
                        track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        track['album']['name'],
                        track.get('external_ids', {}).get('isrc', ''),
                        track['external_urls'].get('spotify', '')
                    ))
                except Exception as e:
                    print(f"      ⚠️ Error saving recent track {track.get('name', 'Unknown')}: {e}")
            
            conn.commit()
            print(f"   ✅ Saved {len(recent['items'])} recent tracks")
        except Exception as e:
            print(f"   ❌ Error fetching recent tracks: {e}")
        
        # 4. Collect Playlists
        print(f"   📝 Fetching playlists...")
        try:
            playlists = sp.current_user_playlists(limit=50)
            for playlist in playlists['items']:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO playlists 
                        (spotify_id, name, description, tracks_total, owner, public, collaborative)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        playlist['id'],
                        playlist['name'],
                        playlist.get('description', ''),
                        playlist['tracks']['total'],
                        playlist['owner']['display_name'],
                        playlist.get('public', False),
                        playlist.get('collaborative', False)
                    ))
                except Exception as e:
                    print(f"      ⚠️ Error saving playlist {playlist.get('name', 'Unknown')}: {e}")
            
            conn.commit()
            print(f"   ✅ Saved {len(playlists['items'])} playlists")
        except Exception as e:
            print(f"   ❌ Error fetching playlists: {e}")
        
        conn.close()
        print(f"✅ Data collection complete for user {user_id}")
        
        # Update user status
        master_db.update_user_analysis_status(user_id, 'pending', 0)
        
    except Exception as e:
        print(f"❌ Error in data collection for user {user_id}: {e}")
        master_db.update_user_analysis_status(user_id, 'failed', 0)

@app.route('/comparison-data')
def get_comparison_data():
    """Get comparison data for all analyzed users"""
    try:
        import comparison_analyzer
        
        # Get all users with completed analysis
        users = master_db.get_all_users()
        completed_users = [u for u in users if u['analysis_status'] == 'completed']
        
        if len(completed_users) < 2:
            return jsonify({
                "error": "Need at least 2 analyzed users for comparison",
                "analyzed_count": len(completed_users)
            }), 400
        
        # Get database paths
        db_paths = [u['db_path'] for u in completed_users]
        
        if len(completed_users) == 2:
            # Two-user comparison
            report = comparison_analyzer.generate_comparison_report(db_paths[0], db_paths[1])
            
            # Add user info
            report['users'] = [
                {
                    'id': completed_users[0]['id'],
                    'display_name': completed_users[0]['display_name'],
                    'spotify_user_id': completed_users[0]['spotify_user_id']
                },
                {
                    'id': completed_users[1]['id'],
                    'display_name': completed_users[1]['display_name'],
                    'spotify_user_id': completed_users[1]['spotify_user_id']
                }
            ]
        else:
            # Multi-user comparison
            report = comparison_analyzer.compare_multiple_users(db_paths)
            
            # Add user info
            report['users'] = [
                {
                    'id': u['id'],
                    'display_name': u['display_name'],
                    'spotify_user_id': u['spotify_user_id']
                }
                for u in completed_users
            ]
        
        return jsonify(report)
        
    except Exception as e:
        print(f"Error generating comparison: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=8888)
