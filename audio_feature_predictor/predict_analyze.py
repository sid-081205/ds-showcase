"""
Audio Feature Predictor - Prediction & Analysis
Predict audio features for new songs and analyze playlists
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path


def load_model(model_path='model_bundle.pkl'):
    """Load trained model and vectorizer"""
    with open(model_path, 'rb') as f:
        bundle = pickle.load(f)
    
    # Load feature names
    features_path = model_path.replace('.pkl', '_features.json')
    with open(features_path, 'r') as f:
        feature_info = json.load(f)
    
    return bundle['model'], bundle['vectorizer'], feature_info['target_features']


def normalize_tags(tags_str):
    """Normalize tags format to match training data"""
    if pd.isna(tags_str) or tags_str == "":
        return ""
    tags = [t.strip().lower().replace(' ', '_').replace('-', '_') 
            for t in str(tags_str).split(',')]
    return ','.join(tags)


def predict_features(model, vectorizer, tags_string, target_features):
    """
    Predict audio features from tags
    
    Args:
        model: Trained model
        vectorizer: TF-IDF vectorizer
        tags_string: Comma-separated tags (e.g., "rock, alternative, 90s")
        target_features: List of feature names
    
    Returns:
        Dict of predicted features
    """
    # Normalize tags
    normalized = normalize_tags(tags_string)
    X = vectorizer.transform([normalized])
    pred = model.predict(X)[0]
    
    return {feat: float(pred[i]) for i, feat in enumerate(target_features)}


def predict_batch(model, vectorizer, df, target_features):
    """
    Predict features for a DataFrame with 'tags' column
    
    Returns:
        DataFrame with original data + predicted features
    """
    # Handle missing tags
    df = df.copy()
    df['tags'] = df['tags'].fillna('').apply(normalize_tags)
    
    X = vectorizer.transform(df['tags'])
    preds = model.predict(X)
    
    for i, feat in enumerate(target_features):
        df[f'pred_{feat}'] = preds[:, i]
    
    return df


# ============================================
# Playlist Analysis
# ============================================

def analyze_playlist_mood(df, feature_cols=None):
    """
    Analyze the overall mood of a playlist
    
    Args:
        df: DataFrame with audio features (predicted or actual)
        feature_cols: List of feature columns to analyze
    
    Returns:
        Dict with mood analysis
    """
    if feature_cols is None:
        # Auto-detect feature columns
        feature_cols = [c for c in df.columns if c in 
                       ['valence', 'energy', 'danceability', 'speechiness',
                        'pred_valence', 'pred_energy', 'pred_danceability', 'pred_speechiness']]
    
    analysis = {}
    
    for col in feature_cols:
        clean_name = col.replace('pred_', '')
        analysis[clean_name] = {
            'mean': float(df[col].mean()),
            'std': float(df[col].std()),
            'min': float(df[col].min()),
            'max': float(df[col].max()),
        }
    
    # Mood classification based on valence + energy quadrant
    valence_col = 'pred_valence' if 'pred_valence' in df.columns else 'valence'
    energy_col = 'pred_energy' if 'pred_energy' in df.columns else 'energy'
    
    if valence_col in df.columns and energy_col in df.columns:
        avg_valence = df[valence_col].mean()
        avg_energy = df[energy_col].mean()
        
        # Quadrant-based mood
        if avg_valence >= 0.5 and avg_energy >= 0.5:
            mood = "Happy/Energetic"
            description = "Upbeat, party vibes, feel-good music"
        elif avg_valence >= 0.5 and avg_energy < 0.5:
            mood = "Peaceful/Content"
            description = "Relaxed, chill, acoustic vibes"
        elif avg_valence < 0.5 and avg_energy >= 0.5:
            mood = "Angry/Intense"
            description = "Aggressive, powerful, intense energy"
        else:
            mood = "Sad/Melancholic"
            description = "Reflective, emotional, introspective"
        
        analysis['overall_mood'] = {
            'quadrant': mood,
            'description': description,
            'valence': avg_valence,
            'energy': avg_energy
        }
    
    return analysis


def compare_albums(df, album_col='album', feature_cols=None):
    """
    Compare audio features across albums
    
    Returns:
        DataFrame with album-level statistics
    """
    if feature_cols is None:
        feature_cols = [c for c in df.columns if 'valence' in c or 'energy' in c or 'danceability' in c]
    
    return df.groupby(album_col)[feature_cols].agg(['mean', 'std']).round(3)


def find_similar_albums(target_album_features, reference_albums_df, top_n=3):
    """
    Find albums most similar to a target album based on audio features
    
    Args:
        target_album_features: Dict of {feature: value} for target album
        reference_albums_df: DataFrame with album-level features
        top_n: Number of similar albums to return
    
    Returns:
        List of (album_name, similarity_score) tuples
    """
    feature_cols = list(target_album_features.keys())
    target_vector = np.array([target_album_features[f] for f in feature_cols])
    
    similarities = []
    for album, row in reference_albums_df.iterrows():
        ref_vector = np.array([row[f] if f in row.index else row[f'pred_{f}'] 
                               for f in feature_cols])
        
        # Euclidean distance (lower = more similar)
        distance = np.linalg.norm(target_vector - ref_vector)
        similarities.append((album, distance))
    
    # Sort by distance (ascending)
    similarities.sort(key=lambda x: x[1])
    
    return similarities[:top_n]


# ============================================
# Pretty printing
# ============================================

def print_analysis(analysis, title="Playlist Analysis"):
    """Pretty print mood analysis"""
    print("=" * 50)
    print(title)
    print("=" * 50)
    
    if 'overall_mood' in analysis:
        mood = analysis['overall_mood']
        print(f"\n🎵 Overall Mood: {mood['quadrant']}")
        print(f"   {mood['description']}")
        print(f"   Valence: {mood['valence']:.3f} | Energy: {mood['energy']:.3f}")
    
    print("\n📊 Feature Statistics:")
    for feat, stats in analysis.items():
        if feat == 'overall_mood':
            continue
        print(f"\n  {feat.capitalize()}:")
        print(f"    Mean: {stats['mean']:.3f} (±{stats['std']:.3f})")
        print(f"    Range: {stats['min']:.3f} - {stats['max']:.3f}")


def print_album_comparison(comparison_df, artist_name=""):
    """Pretty print album comparison"""
    print("=" * 50)
    print(f"Album Comparison{f' - {artist_name}' if artist_name else ''}")
    print("=" * 50)
    print(comparison_df.to_string())


# ============================================
# Example usage
# ============================================

def demo_linkin_park_analysis(model_path='model_bundle.pkl'):
    """
    Demo: Compare Linkin Park's From Zero with older albums
    """
    model, vectorizer, target_features = load_model(model_path)
    
    # Load scraped tags (you need to run lastfm_scraper.py first)
    lp_df = pd.read_csv('linkin_park_tags.csv')
    
    # Predict features
    lp_df = predict_batch(model, vectorizer, lp_df, target_features)
    
    # Compare albums
    print("\n" + "=" * 60)
    print("LINKIN PARK ALBUM COMPARISON")
    print("=" * 60)
    
    album_stats = lp_df.groupby('album').agg({
        'pred_valence': 'mean',
        'pred_energy': 'mean',
        'pred_danceability': 'mean'
    }).round(3)
    
    print("\nAlbum averages (predicted):")
    print(album_stats.sort_values('pred_energy', ascending=False))
    
    # Find which album From Zero is most similar to
    if 'From Zero' in album_stats.index:
        from_zero = album_stats.loc['From Zero']
        print(f"\n🆕 From Zero profile:")
        print(f"   Valence: {from_zero['pred_valence']:.3f}")
        print(f"   Energy: {from_zero['pred_energy']:.3f}")
        print(f"   Danceability: {from_zero['pred_danceability']:.3f}")
        
        # Compare to other albums
        other_albums = album_stats.drop('From Zero')
        from_zero_vec = from_zero.values
        
        distances = []
        for album, row in other_albums.iterrows():
            dist = np.linalg.norm(from_zero_vec - row.values)
            distances.append((album, dist))
        
        distances.sort(key=lambda x: x[1])
        
        print(f"\n📊 From Zero is most similar to:")
        for i, (album, dist) in enumerate(distances, 1):
            print(f"   {i}. {album} (distance: {dist:.3f})")
    
    return lp_df


def demo_taylor_swift_analysis(model_path='model_bundle.pkl'):
    """
    Demo: Analyze Taylor Swift's evolution across eras
    """
    model, vectorizer, target_features = load_model(model_path)
    
    # Load scraped tags
    ts_df = pd.read_csv('taylor_swift_tags.csv')
    
    # Predict features
    ts_df = predict_batch(model, vectorizer, ts_df, target_features)
    
    print("\n" + "=" * 60)
    print("TAYLOR SWIFT ERA COMPARISON")
    print("=" * 60)
    
    # Define era order
    era_order = ['Fearless', 'Red', '1989', 'folklore', 'evermore', 'Midnights', 'TTPD']
    
    album_stats = ts_df.groupby('album').agg({
        'pred_valence': 'mean',
        'pred_energy': 'mean',
        'pred_danceability': 'mean'
    }).round(3)
    
    # Reorder by era
    album_stats = album_stats.reindex([e for e in era_order if e in album_stats.index])
    
    print("\nEra evolution (predicted features):")
    print(album_stats)
    
    # Identify the "saddest" and "happiest" eras
    saddest = album_stats['pred_valence'].idxmin()
    happiest = album_stats['pred_valence'].idxmax()
    most_energetic = album_stats['pred_energy'].idxmax()
    
    print(f"\n🎭 Era insights:")
    print(f"   Happiest era: {happiest} (valence: {album_stats.loc[happiest, 'pred_valence']:.3f})")
    print(f"   Saddest era: {saddest} (valence: {album_stats.loc[saddest, 'pred_valence']:.3f})")
    print(f"   Most energetic: {most_energetic} (energy: {album_stats.loc[most_energetic, 'pred_energy']:.3f})")
    
    return ts_df


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        print("Running demos...")
        print("\n" + "🎸" * 25)
        demo_linkin_park_analysis()
        print("\n" + "🎤" * 25)  
        demo_taylor_swift_analysis()
    else:
        print("Usage:")
        print("  python predict_analyze.py demo    # Run demo analysis")
        print("\nOr import as module:")
        print("  from predict_analyze import load_model, predict_features, analyze_playlist_mood")
