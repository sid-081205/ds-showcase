import requests
import time
import sqlite3
import os
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database helper
def get_db_connection(db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), 'spotify_data.db')
    return sqlite3.connect(db_path)

session = requests.Session()
session.headers.update({'User-Agent': 'SpotifyMoodAnalyzer/1.0'})

# ============================================
# TIER 1: CSV Matching
# ============================================

def load_merged_data():
    """Load the merged_data.csv file with audio features"""
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'merged_data.csv')
    try:
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"   📁 Loaded {len(df)} tracks from merged_data.csv")
        return df
    except Exception as e:
        print(f"   ⚠️ Could not load merged_data.csv: {e}")
        return None

def normalize_string(s):
    """Normalize string for matching (lowercase, strip whitespace)"""
    if not s:
        return ""
    return str(s).lower().strip()

def match_in_csv(df, track_name, artist_name):
    """
    Try to find a matching track in the CSV data
    Returns audio features dict if found, None otherwise
    """
    if df is None:
        return None
    
    # Normalize search terms - only use track name
    norm_track = normalize_string(track_name)
    
    # Match only by track name
    matches = df[df['name'].str.lower().str.strip() == norm_track]
    
    if len(matches) > 0:
        row = matches.iloc[0]
        # Map CSV columns to our database schema
        # CSV has: danceability, valence, energy, acousticness, instrumentalness, etc.
        # We need: danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed
        
        features = {
            'danceability': float(row['danceability']) if pd.notna(row['danceability']) else 0.5,
            'mood_happy': float(row['valence']) if pd.notna(row['valence']) else 0.5,  # valence ~ happiness
            'mood_sad': 1.0 - float(row['valence']) if pd.notna(row['valence']) else 0.5,  # inverse of valence
            'mood_aggressive': float(row['energy']) if pd.notna(row['energy']) else 0.5,  # energy ~ aggressiveness
            'mood_relaxed': float(row['acousticness']) if pd.notna(row['acousticness']) else 0.5,  # acousticness ~ relaxed
        }
        return features
    
    return None

# ============================================
# TIER 2: MusicBrainz + AcousticBrainz
# ============================================

def get_mbid_by_isrc(isrc):
    if not isrc:
        return None
    url = f"https://musicbrainz.org/ws/2/isrc/{isrc}"
    try:
        response = requests.get(url, params={'fmt': 'json'}, headers=session.headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('recordings'):
                return data['recordings'][0]['id']
    except Exception as e:
        print(f"      Error fetching MBID for ISRC {isrc}: {e}")
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
    except Exception as e:
        print(f"      Error fetching features for MBID {mbid}: {e}")
    return None

# ============================================
# TIER 3: Last.fm Tags
# ============================================

class LastFMScraper:
    BASE_URL = "http://ws.audioscrobbler.com/2.0/"
    
    def __init__(self, api_key, cache_path="lastfm_cache.json"):
        self.api_key = api_key
        self.cache_path = Path(cache_path)
        self.cache = self._load_cache()
        self.request_count = 0
        
    def _load_cache(self):
        """Load cached results"""
        if self.cache_path.exists():
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _make_cache_key(self, artist, track):
        """Create a cache key"""
        return f"{artist.lower()}|||{track.lower()}"
    
    def get_track_tags(self, artist, track, min_count=0):
        """
        Get tags for a track
        
        Args:
            track: Track name
            min_count: Minimum tag count to include (filters low-confidence tags)
        
        Returns:
            List of (tag_name, count) tuples, or None if not found
        """
        cache_key = self._make_cache_key(artist, track)
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Rate limiting: 5 requests per second max
        self.request_count += 1
        if self.request_count % 5 == 0:
            time.sleep(1)
        
        params = {
            'method': 'track.gettoptags',
            'track': track,
            'api_key': self.api_key,
            'format': 'json'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                print(f"      Last.fm API error: {data.get('message', 'Unknown error')}")
                self.cache[cache_key] = None
                return None
            
            if 'toptags' not in data or 'tag' not in data['toptags']:
                self.cache[cache_key] = []
                return []
            
            tags = data['toptags']['tag']
            
            # Handle single tag (comes as dict instead of list)
            if isinstance(tags, dict):
                tags = [tags]
            
            # Extract tag names and counts
            result = []
            for tag in tags:
                name = tag.get('name', '').strip().lower()
                count = int(tag.get('count', 0))
                if name and count >= min_count:
                    result.append((name, count))
            
            self.cache[cache_key] = result
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"      Last.fm request error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"      Last.fm JSON decode error: {e}")
            return None
    
    def close(self):
        """Save cache before closing"""
        self._save_cache()

def derive_features_from_tags(tags):
    """
    Derive audio features from Last.fm tags
    
    Args:
        tags: List of (tag_name, count) tuples
    
    Returns:
        Dict with danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed
    """
    if not tags:
        return None
    
    # Tag mappings to moods/features
    tag_weights = {
        # Danceability
        'dance': {'danceability': 0.9},
        'electronic': {'danceability': 0.8},
        'pop': {'danceability': 0.7},
        'disco': {'danceability': 0.9},
        'funk': {'danceability': 0.8},
        'hip hop': {'danceability': 0.8},
        'hip_hop': {'danceability': 0.8},
        
        # Happy
        'happy': {'mood_happy': 0.9},
        'upbeat': {'mood_happy': 0.8},
        'fun': {'mood_happy': 0.7},
        'party': {'mood_happy': 0.8},
        'energetic': {'mood_happy': 0.7},
        
        # Sad
        'sad': {'mood_sad': 0.9},
        'melancholy': {'mood_sad': 0.8},
        'melancholic': {'mood_sad': 0.8},
        'depressing': {'mood_sad': 0.9},
        'emotional': {'mood_sad': 0.6},
        'dark': {'mood_sad': 0.7},
        
        # Aggressive
        'aggressive': {'mood_aggressive': 0.9},
        'metal': {'mood_aggressive': 0.8},
        'hard rock': {'mood_aggressive': 0.8},
        'hard_rock': {'mood_aggressive': 0.8},
        'punk': {'mood_aggressive': 0.7},
        'hardcore': {'mood_aggressive': 0.9},
        'heavy': {'mood_aggressive': 0.8},
        'intense': {'mood_aggressive': 0.7},
        
        # Relaxed
        'relaxed': {'mood_relaxed': 0.9},
        'chill': {'mood_relaxed': 0.8},
        'chillout': {'mood_relaxed': 0.8},
        'ambient': {'mood_relaxed': 0.9},
        'calm': {'mood_relaxed': 0.9},
        'mellow': {'mood_relaxed': 0.8},
        'acoustic': {'mood_relaxed': 0.7},
        'soft': {'mood_relaxed': 0.7},
        'peaceful': {'mood_relaxed': 0.9},
    }
    
    # Initialize features with neutral values
    features = {
        'danceability': 0.5,
        'mood_happy': 0.5,
        'mood_sad': 0.5,
        'mood_aggressive': 0.5,
        'mood_relaxed': 0.5,
    }
    
    # Accumulate weighted scores
    total_weight = 0
    feature_weights = {k: 0 for k in features.keys()}
    
    for tag_name, tag_count in tags:
        tag_name_normalized = tag_name.lower().replace('_', ' ')
        
        if tag_name_normalized in tag_weights:
            weight = tag_count  # Use tag count as weight
            total_weight += weight
            
            for feature, value in tag_weights[tag_name_normalized].items():
                features[feature] += value * weight
                feature_weights[feature] += weight
    
    # Normalize by weights
    if total_weight > 0:
        for feature in features.keys():
            if feature_weights[feature] > 0:
                features[feature] = features[feature] / feature_weights[feature]
            else:
                features[feature] = 0.5  # Keep neutral if no relevant tags
    
    return features

# ============================================
# Main Processing Logic
# ============================================

def process_table(cursor, conn, table_name, merged_df, lastfm_scraper):
    print(f"   Analyzing table: {table_name}")
    # Get tracks that haven't been analyzed yet
    cursor.execute(f'SELECT id, spotify_id, name, artist, isrc FROM {table_name} WHERE danceability IS NULL')
    tracks = cursor.fetchall()

    if not tracks:
        print(f"   ✅ No new tracks in {table_name} to analyze.")
        return

    total = len(tracks)
    print(f"   📊 Found {total} tracks in {table_name} to analyze.")

    for i, (track_id, sp_id, name, artist, isrc) in enumerate(tracks):
        print(f"   [{i+1}/{total}] Analyzing: {name} - {artist}")
        features = None
        
        # TIER 1: Try CSV matching first
        if merged_df is not None:
            features = match_in_csv(merged_df, name, artist)
            if features:
                print(f"      ✅ Found match in merged_data.csv")
        
        if not features and lastfm_scraper:
            tags = lastfm_scraper.get_track_tags(artist, name, min_count=10)
            if tags:
                features = derive_features_from_tags(tags)
                if features:
                    print(f"      ✅ Derived features from Last.fm tags: {[t[0] for t in tags[:5]]}")
        # TIER 2: Try MusicBrainz + AcousticBrainz
        if not features and isrc:
            mbid = get_mbid_by_isrc(isrc)
            time.sleep(1.0)  # Respect rate limits
            
            if mbid:
                features = get_acoustic_features(mbid)
                time.sleep(1.0)  # Respect rate limits
                if features:
                    print(f"      ✅ Found features via MusicBrainz/AcousticBrainz")
    
        
        # Save features if we found any
        if features:
            cursor.execute(f'''
                UPDATE {table_name} 
                SET danceability = ?, mood_happy = ?, mood_sad = ?, mood_aggressive = ?, mood_relaxed = ?
                WHERE id = ?
            ''', (
                features['danceability'],
                features['mood_happy'],
                features['mood_sad'],
                features['mood_aggressive'],
                features['mood_relaxed'],
                track_id
            ))
            conn.commit()
            print(f"      ✅ Saved features for {name}")
        else:
            print(f"      ⚠️ No features found from any source for {name}")

def main():
    import sys
    
    # Get database path from command-line argument if provided
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if db_path:
        print(f"🚀 Starting Audio DNA Analysis for database: {db_path}")
    else:
        print("🚀 Starting Audio DNA Analysis...")
    
    # Load merged data CSV
    merged_df = load_merged_data()
    
    # Initialize Last.fm scraper if API key is available
    lastfm_api_key = os.getenv('LASTFM_API')
    lastfm_scraper = None
    
    if lastfm_api_key:
        cache_path = os.path.join(os.path.dirname(__file__), 'lastfm_cache.json')
        lastfm_scraper = LastFMScraper(lastfm_api_key, cache_path)
        print("   ✅ Last.fm API initialized")
    else:
        print("   ⚠️ LASTFM_API not found in environment variables - Last.fm fallback disabled")
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Only process top_tracks table
    process_table(cursor, conn, 'top_tracks', merged_df, lastfm_scraper)

    if lastfm_scraper:
        lastfm_scraper.close()
    
    conn.close()
    print("🏁 Analysis complete!")

if __name__ == "__main__":
    main()
