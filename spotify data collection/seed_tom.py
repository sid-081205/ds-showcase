
import sqlite3
import os
import master_db
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DB_PATH = os.path.join(BASE_DIR, 'master_users.db')

def seed_tom():
    # 1. Add Tom to master database
    tom_spotify_id = "tomcrawdon_mock"
    tom_display_name = "Tom Crawdon"
    tom_email = "tom@example.com"
    
    # Check if Tom already exists
    tom = master_db.get_user_by_spotify_id(tom_spotify_id)
    if not tom:
        print("Creating mock user Tom...")
        tom = master_db.add_user(
            spotify_user_id=tom_spotify_id,
            display_name=tom_display_name,
            email=tom_email,
            access_token="mock_token",
            refresh_token="mock_refresh",
            token_expiry=9999999999
        )
    else:
        print("Tom already exists, re-seeding data...")
    
    tom_id = tom['id']
    tom_db_path = tom['db_path']
    
    # 2. Get data from the first user to use as a base
    users = master_db.get_all_users()
    source_user = None
    for u in users:
        if u['spotify_user_id'] != tom_spotify_id and os.path.exists(u['db_path']):
            source_user = u
            break
            
    if not source_user:
        print("No source user found to copy data from!")
        return

    print(f"Copying data from {source_user['display_name']} ({source_user['db_path']})")
    
    # Connect to source and target
    source_conn = sqlite3.connect(source_user['db_path'])
    source_conn.row_factory = sqlite3.Row
    source_cursor = source_conn.cursor()
    
    # Create target DB if it doesn't exist (using the schema from collector)
    # We'll just copy the file then modify it to be safe and easy
    if os.path.exists(tom_db_path):
        os.remove(tom_db_path)
    
    import shutil
    shutil.copy2(source_user['db_path'], tom_db_path)
    
    tom_conn = sqlite3.connect(tom_db_path)
    tom_cursor = tom_conn.cursor()
    
    # 3. Mutate Tom's data to make him "different"
    print("Mutating Tom's music taste...")
    # Shift moods: let's make Tom more "energetic" and "happy" than the source
    
    tables = ['top_tracks', 'recent_tracks']
    for table in tables:
        tom_cursor.execute(f"SELECT id, danceability, mood_happy, mood_sad, mood_aggressive, mood_relaxed FROM {table}")
        tracks = tom_cursor.fetchall()
        for t in tracks:
            tid, d, h, s, a, r = t
            # Tweak values slightly (random walk)
            new_d = min(1.0, max(0.0, (d or 0.5) + random.uniform(-0.2, 0.4)))
            new_h = min(1.0, max(0.0, (h or 0.5) + random.uniform(-0.1, 0.5)))
            new_s = min(1.0, max(0.0, (s or 0.5) + random.uniform(-0.3, 0.1)))
            new_a = min(1.0, max(0.0, (a or 0.5) + random.uniform(-0.1, 0.3)))
            new_r = min(1.0, max(0.0, (r or 0.5) + random.uniform(-0.2, 0.2)))
            
            tom_cursor.execute(f"""
                UPDATE {table} 
                SET danceability = ?, mood_happy = ?, mood_sad = ?, mood_aggressive = ?, mood_relaxed = ?
                WHERE id = ?
            """, (new_d, new_h, new_s, new_a, new_r, tid))
            
    # Also randomly remove some tracks so the libraries aren't identical
    for table in tables:
        tom_cursor.execute(f"SELECT id FROM {table}")
        ids = [row[0] for row in tom_cursor.fetchall()]
        to_delete = random.sample(ids, len(ids) // 3) # Delete 33% of tracks
        for did in to_delete:
            tom_cursor.execute(f"DELETE FROM {table} WHERE id = ?", (did,))

    tom_conn.commit()
    tom_conn.close()
    source_conn.close()
    
    # 4. Set status to completed
    master_db.update_user_analysis_status(tom_id, 'completed', 100)
    print("✅ Tom has been seeded with fake data and marked as completed!")

if __name__ == "__main__":
    seed_tom()
