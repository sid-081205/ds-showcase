"""
Spotify Playlist Import Tool
Input playlist URL -> Get track list -> Scrape Last.fm tags -> Predict mood
"""

import requests
import base64
import re
import pandas as pd
from pathlib import Path


class SpotifyClient:
    """Spotify API Client"""
    
    AUTH_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        """Get access token (Client Credentials Flow)"""
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        
        response = requests.post(
            self.AUTH_URL,
            headers={"Authorization": f"Basic {auth_b64}"},
            data={"grant_type": "client_credentials"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Spotify auth failed: {response.text}")
        
        self.token = response.json()["access_token"]
        print("✅ Spotify Authentication Successful")
    
    def _get(self, endpoint, params=None):
        """Send GET request"""
        response = requests.get(
            f"{self.API_BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {self.token}"},
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_playlist(self, playlist_id):
        """Get playlist info and tracks"""
        # Get playlist basic info
        playlist = self._get(f"playlists/{playlist_id}")
        
        name = playlist["name"]
        description = playlist.get("description", "")
        total_tracks = playlist["tracks"]["total"]
        
        print(f"\n📀 Playlist: {name}")
        print(f"   Total Tracks: {total_tracks}")
        
        # Get all tracks (handle pagination)
        tracks = []
        offset = 0
        limit = 100
        
        while offset < total_tracks:
            result = self._get(
                f"playlists/{playlist_id}/tracks",
                params={"offset": offset, "limit": limit}
            )
            
            for item in result["items"]:
                track = item.get("track")
                if track is None:
                    continue
                
                # Extract artist names (handle multiple artists)
                artists = ", ".join([a["name"] for a in track["artists"]])
                
                tracks.append({
                    "track_id": track["id"],
                    "name": track["name"],
                    "artist": artists,
                    "album": track["album"]["name"],
                    "duration_ms": track["duration_ms"],
                    "popularity": track["popularity"],
                })
            
            offset += limit
            print(f"   Fetched {min(offset, total_tracks)}/{total_tracks} tracks...")
        
        return {
            "name": name,
            "description": description,
            "tracks": pd.DataFrame(tracks)
        }
    
    @staticmethod
    def extract_playlist_id(url_or_id):
        """Extract playlist ID from URL or URI"""
        # Supported formats:
        # - https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
        # - spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
        # - 37i9dQZF1DXcBWIGoYBM5M
        
        patterns = [
            r'playlist[/:]([a-zA-Z0-9]+)',  # URL or URI
            r'^([a-zA-Z0-9]{22})$',          # Raw ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return url_or_id  # Assume it's the ID
    
    
def import_playlist(playlist_url, client_id, client_secret, 
                    lastfm_api_key=None, output_path=None):
    """
    Import Spotify playlist and scrape Last.fm tags
    
    Args:
        playlist_url: Spotify playlist URL or ID
        client_id: Spotify Client ID
        client_secret: Spotify Client Secret
        lastfm_api_key: Last.fm API Key (optional, for fetching tags)
        output_path: Output CSV path (optional)
    
    Returns:
        DataFrame with tracks and tags
    """
    # Connect to Spotify
    spotify = SpotifyClient(client_id, client_secret)
    
    # Extract playlist ID
    playlist_id = SpotifyClient.extract_playlist_id(playlist_url)
    print(f"Playlist ID: {playlist_id}")
    
    # Get playlist
    playlist = spotify.get_playlist(playlist_id)
    df = playlist["tracks"]
    
    # Get Last.fm tags (if API key provided)
    if lastfm_api_key:
        print("\nFetching Last.fm tags...")
        from lastfm_scraper import LastFMScraper
        
        scraper = LastFMScraper(lastfm_api_key)
        
        tags_list = []
        for idx, row in df.iterrows():
            # Use only the first artist
            artist = row["artist"].split(",")[0].strip()
            track = row["name"]
            
            tags_str = scraper.get_tags_string(artist, track)
            tags_list.append(tags_str)
            
            if (idx + 1) % 20 == 0:
                print(f"   Processed {idx + 1}/{len(df)} tracks...")
        
        scraper.close()
        df["tags"] = tags_list
        
        # Stats
        has_tags = df["tags"].str.len() > 0
        print(f"\n✅ Tags Fetch Complete")
        print(f"   With tags: {has_tags.sum()}/{len(df)}")
    
    # Save
    if output_path is None:
        # Use playlist name as filename
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', playlist["name"])
        output_path = f"playlist_{safe_name}.csv"
    
    df.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    
    return df, playlist["name"]


def analyze_spotify_playlist(playlist_url, model_path="model_bundle.pkl"):
    """
    One-click Spotify playlist mood analysis
    
    Requires config.py with keys configured
    """
    from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, LASTFM_API_KEY
    import pickle
    
    # Import playlist
    df, playlist_name = import_playlist(
        playlist_url,
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET,
        LASTFM_API_KEY
    )
    
    # Load model
    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
    model = bundle["model"]
    vectorizer = bundle["vectorizer"]
    
    # Predict
    # Normalize tags format
    def normalize_tags(tags_str):
        if pd.isna(tags_str) or tags_str == "":
            return ""
        tags = [t.strip().lower().replace(' ', '_').replace('-', '_') 
                for t in str(tags_str).split(',')]
        return ','.join(tags)
    
    df["tags"] = df["tags"].fillna("").apply(normalize_tags)
    X = vectorizer.transform(df["tags"])
    
    target_features = ["valence", "energy", "danceability"]
    preds = model.predict(X)
    
    for i, feat in enumerate(target_features):
        df[f"pred_{feat}"] = preds[:, i]
    
    # Analysis
    print("\n" + "=" * 60)
    print(f"🎵 Playlist Analysis: {playlist_name}")
    print("=" * 60)
    
    print(f"\n📊 Overall Mood:")
    for feat in target_features:
        col = f"pred_{feat}"
        print(f"   {feat.capitalize():15} {df[col].mean():.3f} (±{df[col].std():.3f})")
    
    # Mood quadrants
    avg_valence = df["pred_valence"].mean()
    avg_energy = df["pred_energy"].mean()
    
    if avg_valence >= 0.5 and avg_energy >= 0.5:
        mood = "😄 Happy/Energetic"
    elif avg_valence >= 0.5 and avg_energy < 0.5:
        mood = "😌 Peaceful/Content"
    elif avg_valence < 0.5 and avg_energy >= 0.5:
        mood = "😤 Angry/Intense"
    else:
        mood = "😢 Sad/Melancholic"
    
    print(f"\n🎭 Overall Atmosphere: {mood}")
    
    # Happiest / Saddest songs
    print(f"\n🌟 Top 3 Most Positive:")
    top_happy = df.nlargest(3, "pred_valence")[["name", "artist", "pred_valence"]]
    for _, row in top_happy.iterrows():
        print(f"   • {row['name']} - {row['artist']} (valence: {row['pred_valence']:.3f})")
    
    print(f"\n💧 Top 3 Most Melancholic:")
    top_sad = df.nsmallest(3, "pred_valence")[["name", "artist", "pred_valence"]]
    for _, row in top_sad.iterrows():
        print(f"   • {row['name']} - {row['artist']} (valence: {row['pred_valence']:.3f})")
    
    return df


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════╗
║          Spotify Playlist Import Tool                    ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Before use, add to config.py:                           ║
║                                                          ║
║    SPOTIFY_CLIENT_ID = "Your Client ID"                   ║
║    SPOTIFY_CLIENT_SECRET = "Your Client Secret"           ║
║                                                          ║
║  Usage:                                                   ║
║    python spotify_import.py <Playlist URL>                ║
║                                                          ║
║  Example:                                                 ║
║    python spotify_import.py https://open.spotify.com/... ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
        """)
        sys.exit(0)
    
    playlist_url = sys.argv[1]
    
    try:
        analyze_spotify_playlist(playlist_url)
    except ImportError as e:
        if "SPOTIFY" in str(e):
            print("❌ Please configure SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in config.py")
        else:
            raise
