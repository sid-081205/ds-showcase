"""
Data Merger + Playlist Comparison Tools
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ============================================
# 1. Merge Datasets
# ============================================

def merge_datasets(csv_with_tags, csv_with_features, output_path="merged_data.csv"):
    """
    Merge two datasets:
    - csv_with_tags: The one with Last.fm tags (Music Info.csv)
    - csv_with_features: The one with complete audio features (your other spotify csv)
    
    Merge Logic:
    1. Use artist + track_name as key
    2. Prioritize keeping data with tags
    3. Supplement data without tags but with audio features
    """
    
    print("Loading datasets...")
    df_tags = pd.read_csv(csv_with_tags)
    df_features = pd.read_csv(csv_with_features)
    
    print(f"  Tags dataset: {len(df_tags)} rows")
    print(f"  Features dataset: {len(df_features)} rows")
    
    # Normalize column names (handle possible naming differences)
    def normalize_columns(df):
        df.columns = df.columns.str.lower().str.strip()
        # Common column name variations
        rename_map = {
            'track_name': 'name',
            'artist_name': 'artist',
            'artists': 'artist',
        }
        for old, new in rename_map.items():
            if old in df.columns and new not in df.columns:
                df = df.rename(columns={old: new})
        return df
    
    df_tags = normalize_columns(df_tags)
    df_features = normalize_columns(df_features)
    
    # Create merge key
    def create_key(df):
        # Clean artist and name, remove case and space differences
        artist = df['artist'].astype(str).str.lower().str.strip()
        name = df['name'].astype(str).str.lower().str.strip()
        return artist + "|||" + name
    
    df_tags['_merge_key'] = create_key(df_tags)
    df_features['_merge_key'] = create_key(df_features)
    
    # Find songs in df_features but not in df_tags
    existing_keys = set(df_tags['_merge_key'])
    new_songs = df_features[~df_features['_merge_key'].isin(existing_keys)]
    
    print(f"\n  Songs only in features dataset: {len(new_songs)}")
    print(f"  Songs with tags: {len(df_tags)}")
    
    # Merge
    # For new_songs, set tags column to empty (scrape later if needed)
    if 'tags' not in new_songs.columns:
        new_songs = new_songs.copy()
        new_songs['tags'] = ''
    
    # Ensure both dfs have same columns
    common_cols = list(set(df_tags.columns) & set(new_songs.columns))
    
    merged = pd.concat([
        df_tags[common_cols],
        new_songs[common_cols]
    ], ignore_index=True)
    
    # Delete temporary column
    if '_merge_key' in merged.columns:
        merged = merged.drop(columns=['_merge_key'])
    
    # Save
    merged.to_csv(output_path, index=False)
    print(f"\n✅ Merged dataset saved to {output_path}")
    print(f"   Total rows: {len(merged)}")
    
    # Stats
    has_tags = merged['tags'].notna() & (merged['tags'] != '')
    print(f"   With tags: {has_tags.sum()}")
    print(f"   Without tags (need scraping): {(~has_tags).sum()}")
    
    return merged


# ============================================
# 2. Playlist Comparison
# ============================================

def load_playlist(source, model_bundle_path='model_bundle.pkl'):
    """
    Load playlist, supports multiple input formats:
    - CSV file path
    - DataFrame
    - List of dicts [{'artist': '...', 'track': '...'}, ...]
    """
    if isinstance(source, str) and source.endswith('.csv'):
        df = pd.read_csv(source)
    elif isinstance(source, pd.DataFrame):
        df = source.copy()
    elif isinstance(source, list):
        df = pd.DataFrame(source)
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")
    
    return df


def compare_playlists(playlist1, playlist2, name1="Playlist 1", name2="Playlist 2", 
                      model_bundle_path='model_bundle.pkl'):
    """
    Compare emotional features of two playlists
    
    Args:
        playlist1, playlist2: CSV path / DataFrame / dict list
        name1, name2: Playlist names (for display)
    
    Returns:
        Comparison result dict
    """
    import pickle
    
    # Load model
    with open(model_bundle_path, 'rb') as f:
        bundle = pickle.load(f)
    model = bundle['model']
    vectorizer = bundle['vectorizer']
    
    # Load playlists
    df1 = load_playlist(playlist1)
    df2 = load_playlist(playlist2)
    
    # Target features
    target_features = ['valence', 'energy', 'danceability']
    
    def get_features(df):
        """Get or predict audio features"""
        results = {}
        
        # Check if audio features already exist
        has_features = all(f in df.columns for f in target_features)
        has_tags = 'tags' in df.columns
        
        if has_features:
            # Use existing features
            for f in target_features:
                results[f] = df[f].mean()
            results['source'] = 'actual'
        elif has_tags:
            # Predict using tags
            # Normalize tags format
            def normalize_tags(tags_str):
                if pd.isna(tags_str) or tags_str == "":
                    return ""
                tags = [t.strip().lower().replace(' ', '_').replace('-', '_') 
                        for t in str(tags_str).split(',')]
                return ','.join(tags)
            
            df['tags'] = df['tags'].fillna('').apply(normalize_tags)
            X = vectorizer.transform(df['tags'])
            preds = model.predict(X)
            for i, f in enumerate(target_features):
                results[f] = preds[:, i].mean()
            results['source'] = 'predicted'
        else:
            raise ValueError("DataFrame needs either audio features or tags column")
        
        return results
    
    feat1 = get_features(df1)
    feat2 = get_features(df2)
    
    # Calculate difference
    comparison = {
        'playlist1': {'name': name1, 'tracks': len(df1), **feat1},
        'playlist2': {'name': name2, 'tracks': len(df2), **feat2},
        'difference': {}
    }
    
    for f in target_features:
        diff = feat1[f] - feat2[f]
        comparison['difference'][f] = diff
    
    # Emotion interpretation
    val_diff = comparison['difference']['valence']
    energy_diff = comparison['difference']['energy']
    
    interpretations = []
    
    if abs(val_diff) > 0.1:
        if val_diff > 0:
            interpretations.append(f"{name1} is more positive/happy than {name2} (valence +{val_diff:.2f})")
        else:
            interpretations.append(f"{name1} is more negative/melancholic than {name2} (valence {val_diff:.2f})")
    
    if abs(energy_diff) > 0.1:
        if energy_diff > 0:
            interpretations.append(f"{name1} is more energetic than {name2} (energy +{energy_diff:.2f})")
        else:
            interpretations.append(f"{name1} is calmer/more soothing than {name2} (energy {energy_diff:.2f})")
    
    if not interpretations:
        interpretations.append("Both playlists have similar emotional features")
    
    comparison['interpretation'] = interpretations
    
    return comparison


def print_comparison(comparison):
    """Print comparison results"""
    p1 = comparison['playlist1']
    p2 = comparison['playlist2']
    
    print("\n" + "=" * 60)
    print("🎵 Playlist Emotional Comparison")
    print("=" * 60)
    
    print(f"\n📀 {p1['name']} ({p1['tracks']} tracks)")
    print(f"   Valence:      {p1['valence']:.3f}")
    print(f"   Energy:       {p1['energy']:.3f}")
    print(f"   Danceability: {p1['danceability']:.3f}")
    print(f"   [Source: {p1['source']}]")
    
    print(f"\n📀 {p2['name']} ({p2['tracks']} tracks)")
    print(f"   Valence:      {p2['valence']:.3f}")
    print(f"   Energy:       {p2['energy']:.3f}")
    print(f"   Danceability: {p2['danceability']:.3f}")
    print(f"   [Source: {p2['source']}]")
    
    print("\n" + "-" * 60)
    print("📊 Difference Analysis:")
    for interp in comparison['interpretation']:
        print(f"   • {interp}")
    
    # Visualization (ASCII art)
    print("\n" + "-" * 60)
    print("📈 Valence-Energy Quadrant:")
    print("""
                    High Energy
                         │
           Angry/        │        Happy/
           Intense       │        Energetic
                         │
    ─────────────────────┼───────────────────── High Valence
                         │
           Sad/          │        Peaceful/
           Melancholic   │        Content
                         │
                    Low Energy
    """)
    
    def get_quadrant(v, e):
        if v >= 0.5 and e >= 0.5:
            return "Happy/Energetic (Top Right)"
        elif v >= 0.5 and e < 0.5:
            return "Peaceful/Content (Bottom Right)"
        elif v < 0.5 and e >= 0.5:
            return "Angry/Intense (Top Left)"
        else:
            return "Sad/Melancholic (Bottom Left)"
    
    q1 = get_quadrant(p1['valence'], p1['energy'])
    q2 = get_quadrant(p2['valence'], p2['energy'])
    
    print(f"   {p1['name']}: {q1}")
    print(f"   {p2['name']}: {q2}")


# ============================================
# 3. Scrape missing tags on demand
# ============================================

def fill_missing_tags(df, api_key, output_path=None):
    """
    Scrape Last.fm tags for songs without tags
    """
    from lastfm_scraper import LastFMScraper
    
    # Find rows with missing tags
    missing_mask = df['tags'].isna() | (df['tags'] == '')
    missing_count = missing_mask.sum()
    
    if missing_count == 0:
        print("✅ All songs have tags, no scraping needed")
        return df
    
    print(f"Need to scrape tags for {missing_count} songs...")
    
    scraper = LastFMScraper(api_key)
    
    # Scrape
    for idx in df[missing_mask].index:
        artist = df.loc[idx, 'artist']
        track = df.loc[idx, 'name']
        
        tags_str = scraper.get_tags_string(artist, track)
        df.loc[idx, 'tags'] = tags_str
        
        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1} songs...")
    
    scraper.close()
    
    # Save
    if output_path:
        df.to_csv(output_path, index=False)
        print(f"✅ Saved to {output_path}")
    
    return df


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════╗
║           Playlist Emotion Analysis Tool - Guide         ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. Merge Datasets:                                      ║
║     python playlist_tools.py merge data1.csv data2.csv   ║
║                                                          ║
║  2. Compare Two Playlists:                               ║
║     python playlist_tools.py compare p1.csv p2.csv       ║
║                                                          ║
║  3. Scrape Tags for Missing Songs:                       ║
║     python playlist_tools.py fill data.csv               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "merge" and len(sys.argv) >= 4:
        merge_datasets(sys.argv[2], sys.argv[3])
    
    elif cmd == "compare" and len(sys.argv) >= 4:
        result = compare_playlists(
            sys.argv[2], sys.argv[3],
            name1=Path(sys.argv[2]).stem,
            name2=Path(sys.argv[3]).stem
        )
        print_comparison(result)
    
    elif cmd == "fill" and len(sys.argv) >= 3:
        from config import LASTFM_API_KEY
        df = pd.read_csv(sys.argv[2])
        fill_missing_tags(df, LASTFM_API_KEY, sys.argv[2])
    
    else:
        print("Invalid arguments, please check the guide above")
