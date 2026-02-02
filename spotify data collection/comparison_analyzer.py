"""
Comparison Analyzer - Compare music taste between multiple users
Analyzes mood profiles, artist/genre overlap, and generates compatibility scores
"""

import sqlite3
import numpy as np
from collections import Counter
import json
import os
import pandas as pd
from sklearn.neighbors import NearestNeighbors

def load_user_data(db_path):
    """Load analyzed data from a user's database"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get analyzed tracks with mood data
        cursor.execute("""
            SELECT name, artist, danceability, mood_happy, mood_sad, 
                   mood_aggressive, mood_relaxed
            FROM top_tracks 
            WHERE danceability IS NOT NULL
        """)
        tracks = [dict(row) for row in cursor.fetchall()]
        
        # Get top artists
        cursor.execute("""
            SELECT name, genres, popularity, followers
            FROM artists 
            WHERE artist_type = 'top'
            ORDER BY popularity DESC
        """)
        artists = [dict(row) for row in cursor.fetchall()]
        
        # Calculate average mood profile
        if tracks:
            mood_profile = {
                'danceability': np.mean([t['danceability'] for t in tracks if t['danceability']]),
                'happy': np.mean([t['mood_happy'] for t in tracks if t['mood_happy']]),
                'sad': np.mean([t['mood_sad'] for t in tracks if t['mood_sad']]),
                'aggressive': np.mean([t['mood_aggressive'] for t in tracks if t['mood_aggressive']]),
                'relaxed': np.mean([t['mood_relaxed'] for t in tracks if t['mood_relaxed']])
            }
        else:
            mood_profile = None
        
        # Extract genres
        all_genres = []
        for artist in artists:
            if artist['genres']:
                all_genres.extend([g.strip() for g in artist['genres'].split(',')])
        
        genre_counts = Counter(all_genres)
        top_genres = [{'name': g, 'count': c} for g, c in genre_counts.most_common(10)]
        
        # Extract artist names
        artist_names = [a['name'] for a in artists]
        
        conn.close()
        
        return {
            'tracks': tracks,
            'artists': artists,
            'artist_names': set(artist_names),
            'mood_profile': mood_profile,
            'genres': top_genres,
            'genre_set': set(all_genres)
        }
        
    except Exception as e:
        print(f"Error loading data from {db_path}: {e}")
        return None

def calculate_mood_similarity(user1_data, user2_data):
    """Calculate cosine similarity between two mood profiles"""
    if not user1_data['mood_profile'] or not user2_data['mood_profile']:
        return 0.0
    
    mood1 = user1_data['mood_profile']
    mood2 = user2_data['mood_profile']
    
    # Create mood vectors
    vector1 = np.array([
        mood1['danceability'],
        mood1['happy'],
        mood1['sad'],
        mood1['aggressive'],
        mood1['relaxed']
    ])
    
    vector2 = np.array([
        mood2['danceability'],
        mood2['happy'],
        mood2['sad'],
        mood2['aggressive'],
        mood2['relaxed']
    ])
    
    # Calculate cosine similarity
    dot_product = np.dot(vector1, vector2)
    magnitude1 = np.linalg.norm(vector1)
    magnitude2 = np.linalg.norm(vector2)
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    similarity = dot_product / (magnitude1 * magnitude2)
    
    # Convert to percentage (0-100)
    return (similarity + 1) / 2 * 100  # Normalize from [-1, 1] to [0, 100]

def find_common_artists(user1_data, user2_data):
    """Find artists that both users listen to"""
    common = user1_data['artist_names'].intersection(user2_data['artist_names'])
    
    # Get full artist data for common artists
    common_artists = []
    for artist in user1_data['artists']:
        if artist['name'] in common:
            common_artists.append(artist)
    
    return common_artists

def find_common_genres(user1_data, user2_data):
    """Find genres that both users listen to"""
    common = user1_data['genre_set'].intersection(user2_data['genre_set'])
    
    # Get counts for common genres
    common_genres = []
    for genre_data in user1_data['genres']:
        if genre_data['name'] in common:
            common_genres.append(genre_data)
    
    return sorted(common_genres, key=lambda x: x['count'], reverse=True)

def calculate_taste_overlap(user1_data, user2_data):
    """Calculate overall taste overlap percentage"""
    # Artist overlap
    total_artists = len(user1_data['artist_names'].union(user2_data['artist_names']))
    common_artists = len(user1_data['artist_names'].intersection(user2_data['artist_names']))
    artist_overlap = (common_artists / total_artists * 100) if total_artists > 0 else 0
    
    # Genre overlap
    total_genres = len(user1_data['genre_set'].union(user2_data['genre_set']))
    common_genres = len(user1_data['genre_set'].intersection(user2_data['genre_set']))
    genre_overlap = (common_genres / total_genres * 100) if total_genres > 0 else 0
    
    # Weighted average (60% genre, 40% artist)
    overall_overlap = (genre_overlap * 0.6 + artist_overlap * 0.4)
    
    return {
        'overall': overall_overlap,
        'artist_overlap': artist_overlap,
        'genre_overlap': genre_overlap,
        'common_artists_count': common_artists,
        'common_genres_count': common_genres
    }

def calculate_compatibility_score(user1_data, user2_data):
    """Calculate overall compatibility score (0-100)"""
    # Mood similarity (40% weight)
    mood_sim = calculate_mood_similarity(user1_data, user2_data)
    
    # Taste overlap (60% weight)
    taste = calculate_taste_overlap(user1_data, user2_data)
    
    # Weighted score
    compatibility = (mood_sim * 0.4) + (taste['overall'] * 0.6)
    
    return round(compatibility, 1)

def find_unique_preferences(user1_data, user2_data):
    """Find what's unique to each user"""
    user1_unique_artists = user1_data['artist_names'] - user2_data['artist_names']
    user2_unique_artists = user2_data['artist_names'] - user1_data['artist_names']
    
    user1_unique_genres = user1_data['genre_set'] - user2_data['genre_set']
    user2_unique_genres = user2_data['genre_set'] - user1_data['genre_set']
    
    return {
        'user1_unique_artists': list(user1_unique_artists)[:10],
        'user2_unique_artists': list(user2_unique_artists)[:10],
        'user1_unique_genres': list(user1_unique_genres)[:10],
        'user2_unique_genres': list(user2_unique_genres)[:10]
    }

def get_joint_recommendations(user1_data, user2_data, limit=5):
    """Recommend songs based on joint preference of both users using PCA"""
    if not user1_data['mood_profile'] or not user2_data['mood_profile']:
        return []
    
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'merged_data.csv')
    if not os.path.exists(csv_path):
        print(f"⚠️ Recommendation failed: {csv_path} not found")
        return []
    
    try:
        # 1. Load the dataset
        df = pd.read_csv(csv_path, low_memory=False)
        
        # 3. Features for comparison (Using all 4 directly, no PCA)
        features = ['danceability', 'valence', 'energy', 'acousticness']
        data = df[features].fillna(0.5).values
        
        # 4. Create the joint target vector from both users
        mood1 = user1_data['mood_profile']
        mood2 = user2_data['mood_profile']
        
        joint_mood = np.array([
            (mood1['danceability'] + mood2['danceability']) / 2,
            (mood1['happy'] + mood2['happy']) / 2,
            (mood1['aggressive'] + mood2['aggressive']) / 2,
            (mood1['relaxed'] + mood2['relaxed']) / 2
        ]).reshape(1, -1)
        
        # 5. Find nearest neighbors in original 4D feature space
        nn = NearestNeighbors(n_neighbors=limit + 20) # Get more to filter duplicates/existing
        nn.fit(data)
        distances, indices = nn.kneighbors(joint_mood)
        
        # 6. Extract results
        recommendations = []
        seen = set()
        
        # Don't recommend songs they already have (simplified check)
        existing_names = set(t['name'].lower() for t in user1_data['tracks'] + user2_data['tracks'])
        
        for idx in indices[0]:
            row = df.iloc[idx]
            name = row['name']
            artist = row['artist']
            
            if name.lower() not in existing_names and name.lower() not in seen:
                recommendations.append({
                    'name': name,
                    'artist': artist,
                    'track_id': str(row.get('track_id', '')),
                    'match_score': round(100 - (distances[0][0] * 100), 1) # Pseudo match score
                })
                seen.add(name.lower())
                if len(recommendations) >= limit:
                    break
        
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return []

def generate_comparison_report(user1_db, user2_db):
    """Generate a comprehensive comparison report for two users"""
    print("🔍 Loading user data...")
    user1_data = load_user_data(user1_db)
    user2_data = load_user_data(user2_db)
    
    if not user1_data or not user2_data:
        return {"error": "Failed to load user data"}
    
    print("📊 Calculating compatibility...")
    compatibility = calculate_compatibility_score(user1_data, user2_data)
    
    print("🎵 Finding common ground...")
    common_artists = find_common_artists(user1_data, user2_data)
    common_genres = find_common_genres(user1_data, user2_data)
    
    print("🎯 Analyzing differences...")
    taste_overlap = calculate_taste_overlap(user1_data, user2_data)
    unique_prefs = find_unique_preferences(user1_data, user2_data)
    
    print("💯 Calculating mood similarity...")
    mood_similarity = calculate_mood_similarity(user1_data, user2_data)
    
    print("🤖 Generating ML recommendations...")
    recommendations = get_joint_recommendations(user1_data, user2_data)
    
    report = {
        'compatibility_score': compatibility,
        'mood_similarity': round(mood_similarity, 1),
        'taste_overlap': taste_overlap,
        'common_artists': [{'name': a['name'], 'popularity': a['popularity']} for a in common_artists[:10]],
        'common_genres': common_genres[:10],
        'unique_preferences': unique_prefs,
        'joint_recommendations': recommendations,
        'mood_profiles': {
            'user1': user1_data['mood_profile'],
            'user2': user2_data['mood_profile']
        },
        'stats': {
            'user1_tracks': len(user1_data['tracks']),
            'user2_tracks': len(user2_data['tracks']),
            'user1_artists': len(user1_data['artists']),
            'user2_artists': len(user2_data['artists'])
        }
    }
    
    print("✅ Comparison complete!")
    return report

def compare_multiple_users(db_paths):
    """Compare multiple users (3+)"""
    # Load all user data
    users_data = []
    for db_path in db_paths:
        data = load_user_data(db_path)
        if data:
            users_data.append(data)
    
    if len(users_data) < 2:
        return {"error": "Need at least 2 users for comparison"}
    
    # Find common artists across all users
    common_artists = users_data[0]['artist_names']
    for user_data in users_data[1:]:
        common_artists = common_artists.intersection(user_data['artist_names'])
    
    # Find common genres across all users
    common_genres = users_data[0]['genre_set']
    for user_data in users_data[1:]:
        common_genres = common_genres.intersection(user_data['genre_set'])
    
    # Calculate average compatibility
    compatibilities = []
    for i in range(len(users_data)):
        for j in range(i + 1, len(users_data)):
            comp = calculate_compatibility_score(users_data[i], users_data[j])
            compatibilities.append(comp)
    
    avg_compatibility = np.mean(compatibilities) if compatibilities else 0
    
    return {
        'user_count': len(users_data),
        'average_compatibility': round(avg_compatibility, 1),
        'common_artists': list(common_artists)[:10],
        'common_genres': list(common_genres)[:10],
        'pairwise_compatibilities': compatibilities
    }

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python comparison_analyzer.py <user1_db> <user2_db> [user3_db ...]")
        sys.exit(1)
    
    if len(sys.argv) == 3:
        # Two users
        report = generate_comparison_report(sys.argv[1], sys.argv[2])
        print(json.dumps(report, indent=2))
    else:
        # Multiple users
        report = compare_multiple_users(sys.argv[1:])
        print(json.dumps(report, indent=2))
