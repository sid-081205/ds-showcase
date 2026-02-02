# Audio Feature Analyzer - Three-Tier System

## Overview

The `analyzer.py` script extracts audio features (danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed) for tracks in your Spotify database using a sophisticated three-tier fallback system.

## How It Works

### Tier 1: CSV Matching (Fastest)
- Matches song name and artist against `merged_data.csv` (157,750 tracks)
- Maps Spotify audio features to mood features:
  - `danceability` → `danceability`
  - `valence` → `mood_happy`
  - `1.0 - valence` → `mood_sad`
  - `energy` → `mood_aggressive`
  - `acousticness` → `mood_relaxed`

### Tier 2: MusicBrainz + AcousticBrainz (Reliable)
- Uses ISRC codes to find MusicBrainz IDs
- Fetches high-level audio features from AcousticBrainz API
- Provides scientifically-derived mood and feature data

### Tier 3: Last.fm Tags (Creative Fallback)
- Fetches genre/mood tags from Last.fm API
- Derives audio features based on tag mappings:
  - **Danceability**: dance, electronic, pop, disco, funk, hip hop
  - **Happy**: happy, upbeat, fun, party, energetic
  - **Sad**: sad, melancholy, depressing, emotional, dark
  - **Aggressive**: aggressive, metal, hard rock, punk, hardcore, heavy, intense
  - **Relaxed**: relaxed, chill, ambient, calm, mellow, acoustic, soft, peaceful
- Uses tag counts as weights for more accurate feature estimation
- Caches results in `lastfm_cache.json` to minimize API calls

## Setup

### 1. Install Dependencies
```bash
pip3 install pandas python-dotenv requests
```

### 2. Environment Variables
Add to your `.env` file:
```bash
LASTFM_API=your_lastfm_api_key
LASTFM_SECRET=your_lastfm_secret
```

Get your Last.fm API key at: https://www.last.fm/api/account/create

### 3. Ensure merged_data.csv Exists
The script expects `merged_data.csv` in the parent directory with columns:
- `name` (track name)
- `artist` (artist name)
- `danceability`, `valence`, `energy`, `acousticness` (Spotify features)

## Usage

```bash
cd "spotify data collection"
python3 analyzer.py
```

The script will:
1. Load merged_data.csv
2. Initialize Last.fm API
3. Process all tracks in `recent_tracks` and `top_tracks` tables
4. Save audio features to the database
5. Create/update `lastfm_cache.json` for faster subsequent runs

## Output Example

```
🚀 Starting Audio DNA Analysis...
   📁 Loaded 157750 tracks from merged_data.csv
   ✅ Last.fm API initialized
   Analyzing table: recent_tracks
   📊 Found 36 tracks in recent_tracks to analyze.
   [1/36] Analyzing: Vienna - Billy Joel
      ✅ Found match in merged_data.csv
      ✅ Saved features for Vienna
   [2/36] Analyzing: Beedi - Vishal Bhardwaj
      ✅ Found features via MusicBrainz/AcousticBrainz
      ✅ Saved features for Beedi
   [3/36] Analyzing: I Think I Like You Better When You're Gone - Reneé Rapp
      ✅ Derived features from Last.fm tags: ['pop', 'indie', 'female']
      ✅ Saved features for I Think I Like You Better When You're Gone
```

## Performance

- **CSV Matching**: Instant (no API calls)
- **MusicBrainz/AcousticBrainz**: ~2 seconds per track (rate limiting)
- **Last.fm**: ~0.2 seconds per track (5 requests/second limit)
- **Caching**: Last.fm results are cached permanently

## Database Schema

The analyzer updates these columns in `recent_tracks` and `top_tracks`:
- `danceability` (REAL)
- `mood_happy` (REAL)
- `mood_sad` (REAL)
- `mood_aggressive` (REAL)
- `mood_relaxed` (REAL)

All values are between 0.0 and 1.0.

## Troubleshooting

### "Could not load merged_data.csv"
- Ensure `merged_data.csv` exists in the parent directory
- The script will continue with Tier 2 and 3 if CSV is missing

### "LASTFM_API not found in environment variables"
- Add your Last.fm API key to `.env`
- The script will continue with Tier 1 and 2 if Last.fm is unavailable

### "No features found from any source"
- Track is not in CSV
- No ISRC code available for MusicBrainz lookup
- Last.fm has no tags for this track
- Consider manually adding features or using a different data source

## Rate Limits

- **MusicBrainz**: 1 request/second (enforced by script)
- **AcousticBrainz**: 1 request/second (enforced by script)
- **Last.fm**: 5 requests/second (enforced by script)

## Cache Management

The `lastfm_cache.json` file stores all Last.fm API responses. To reset:
```bash
rm lastfm_cache.json
```

The cache uses the format: `artist|||track` as keys.
