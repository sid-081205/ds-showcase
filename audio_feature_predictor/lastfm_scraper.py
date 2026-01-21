"""
Last.fm Tag Scraper
Fetch tags for songs not in the training dataset
"""

import requests
import time
import json
import pandas as pd
from pathlib import Path


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
            artist: Artist name
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
            'artist': artist,
            'track': track,
            'api_key': self.api_key,
            'format': 'json'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                print(f"  API error for {artist} - {track}: {data.get('message', 'Unknown error')}")
                self.cache[cache_key] = None
                return None
            
            if 'toptags' not in data or 'tag' not in data['toptags']:
                print(f"  No tags found for {artist} - {track}")
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
            print(f"  Request error for {artist} - {track}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"  JSON decode error for {artist} - {track}: {e}")
            return None
    
    def get_tags_string(self, artist, track, top_n=10, min_count=0):
        """
        Get tags as a comma-separated string (format matching training data)
        """
        tags = self.get_track_tags(artist, track, min_count=min_count)
        
        if not tags:
            return ""
        
        # Take top N tags by count
        top_tags = sorted(tags, key=lambda x: x[1], reverse=True)[:top_n]
        
        # Normalize: Replace spaces with underscores to match training data format
        normalized = [t[0].replace(' ', '_').replace('-', '_') for t in top_tags]
        return ', '.join(normalized)
    
    def fetch_artist_discography(self, artist, tracks):
        """
        Fetch tags for multiple tracks by an artist
        
        Args:
            artist: Artist name
            tracks: List of track names
        
        Returns:
            DataFrame with track, tags columns
        """
        results = []
        
        print(f"Fetching tags for {len(tracks)} tracks by {artist}...")
        
        for i, track in enumerate(tracks):
            tags_str = self.get_tags_string(artist, track)
            results.append({
                'artist': artist,
                'track': track,
                'tags': tags_str
            })
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(tracks)} tracks")
                self._save_cache()  # Periodic save
        
        self._save_cache()  # Final save
        
        return pd.DataFrame(results)
    
    def close(self):
        """Save cache before closing"""
        self._save_cache()
        print(f"Cache saved: {len(self.cache)} entries")


# ============================================
# Convenience functions
# ============================================

def fetch_taylor_swift_discography(api_key):
    """Fetch tags for Taylor Swift's major albums"""
    
    # Selected tracks from different albums for demonstration
    tracks = {
        # 1989 (synth-pop era)
        "Shake It Off": "1989",
        "Blank Space": "1989",
        "Style": "1989",
        "Bad Blood": "1989",
        "Wildest Dreams": "1989",
        
        # folklore/evermore (indie folk era)
        "cardigan": "folklore",
        "the 1": "folklore",
        "exile": "folklore",
        "august": "folklore",
        "betty": "folklore",
        "willow": "evermore",
        "champagne problems": "evermore",
        "no body, no crime": "evermore",
        
        # Midnights
        "Anti-Hero": "Midnights",
        "Lavender Haze": "Midnights",
        "Midnight Rain": "Midnights",
        "Maroon": "Midnights",
        
        # Tortured Poets Department
        "Fortnight": "TTPD",
        "Fresh Out the Slammer": "TTPD",
        "Down Bad": "TTPD",
        "So Long, London": "TTPD",
        
        # Earlier albums
        "Love Story": "Fearless",
        "You Belong with Me": "Fearless",
        "We Are Never Getting Back Together": "Red",
        "All Too Well": "Red",
        "22": "Red",
    }
    
    scraper = LastFMScraper(api_key)
    
    results = []
    for track, album in tracks.items():
        tags_str = scraper.get_tags_string("Taylor Swift", track)
        results.append({
            'artist': 'Taylor Swift',
            'track': track,
            'album': album,
            'tags': tags_str
        })
        print(f"  {track} ({album}): {tags_str[:50]}...")
    
    scraper.close()
    
    df = pd.DataFrame(results)
    df.to_csv('taylor_swift_tags.csv', index=False)
    print(f"\nSaved to taylor_swift_tags.csv")
    
    return df


def fetch_linkin_park_discography(api_key):
    """Fetch tags for Linkin Park albums including From Zero"""
    
    tracks = {
        # Hybrid Theory
        "One Step Closer": "Hybrid Theory",
        "Crawling": "Hybrid Theory",
        "In the End": "Hybrid Theory",
        "Papercut": "Hybrid Theory",
        
        # Meteora
        "Numb": "Meteora",
        "Faint": "Meteora",
        "Somewhere I Belong": "Meteora",
        "Breaking the Habit": "Meteora",
        
        # Minutes to Midnight
        "What I've Done": "Minutes to Midnight",
        "Bleed It Out": "Minutes to Midnight",
        "Shadow of the Day": "Minutes to Midnight",
        "Leave Out All the Rest": "Minutes to Midnight",
        
        # A Thousand Suns
        "The Catalyst": "A Thousand Suns",
        "Waiting for the End": "A Thousand Suns",
        "Burning in the Skies": "A Thousand Suns",
        
        # Living Things
        "Burn It Down": "Living Things",
        "Lost in the Echo": "Living Things",
        "Castle of Glass": "Living Things",
        
        # From Zero (2024 - new album with Emily Armstrong)
        "The Emptiness Machine": "From Zero",
        "Heavy Is the Crown": "From Zero",
        "Cut the Bridge": "From Zero",
        "Overflow": "From Zero",
        "Over Each Other": "From Zero",
    }
    
    scraper = LastFMScraper(api_key)
    
    results = []
    for track, album in tracks.items():
        tags_str = scraper.get_tags_string("Linkin Park", track)
        results.append({
            'artist': 'Linkin Park',
            'track': track,
            'album': album,
            'tags': tags_str
        })
        print(f"  {track} ({album}): {tags_str[:50] if tags_str else 'NO TAGS'}...")
    
    scraper.close()
    
    df = pd.DataFrame(results)
    df.to_csv('linkin_park_tags.csv', index=False)
    print(f"\nSaved to linkin_park_tags.csv")
    
    return df


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    # check config.py for API key
    try:
        from config import LASTFM_API_KEY
    except ImportError:
        print("❌ config.py not found!")
        print("   Please create config.py and fill in:")
        print('   LASTFM_API_KEY = "Your API Key"')
        exit(1)
    
    if LASTFM_API_KEY == "在这里填你的Last.fm API Key" or LASTFM_API_KEY == "Paste your keys here":
        print("❌ Please fill in your Last.fm API Key in config.py")
        exit(1)
    
    print("✅ API Key loaded")
    print("\n" + "="*50)
    print("Starting crawl for Taylor Swift...")
    print("="*50)
    fetch_taylor_swift_discography(LASTFM_API_KEY)
    
    print("\n" + "="*50)
    print("Starting crawl for Linkin Park...")
    print("="*50)
    fetch_linkin_park_discography(LASTFM_API_KEY)
