import requests
import time
import sqlite3
import os

# Database helper
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'spotify_data.db')
    return sqlite3.connect(db_path)

session = requests.Session()
session.headers.update({'User-Agent': 'SpotifyMoodAnalyzer/1.0'})

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
        print(f"Error fetching MBID for ISRC {isrc}: {e}")
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
        print(f"Error fetching features for MBID {mbid}: {e}")
    return None

def process_table(cursor, conn, table_name):
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
        
        mbid = get_mbid_by_isrc(isrc)
        time.sleep(1.0) # Respect rate limits

        if mbid:
            features = get_acoustic_features(mbid)
            time.sleep(1.0) # Respect rate limits
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
                print(f"      ⚠️ No acoustic features found for {name}")
        else:
            print(f"      ⚠️ No MBID found for ISRC {isrc} ({name})")

def main():
    print("🚀 Starting Audio DNA Analysis...")
    conn = get_db_connection()
    cursor = conn.cursor()

    process_table(cursor, conn, 'recent_tracks')
    process_table(cursor, conn, 'top_tracks')

    conn.close()
    print("🏁 Analysis complete!")

if __name__ == "__main__":
    main()
