"""
Master Database Manager for Multi-User Spotify Comparison
Handles user management and tracks individual user databases
"""

import sqlite3
import os
from datetime import datetime

MASTER_DB_PATH = os.path.join(os.path.dirname(__file__), 'master_users.db')

def init_master_db():
    """Initialize the master database with users table"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_user_id TEXT UNIQUE NOT NULL,
            display_name TEXT,
            email TEXT,
            db_path TEXT NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry INTEGER,
            analysis_status TEXT DEFAULT 'pending',
            analysis_progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Master database initialized")

def add_user(spotify_user_id, display_name, email, access_token, refresh_token, token_expiry):
    """Add a new user to the master database"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create unique database path for this user
    db_filename = f"spotify_data_user_{spotify_user_id}.db"
    db_path = os.path.join(os.path.dirname(__file__), db_filename)
    
    try:
        cursor.execute("""
            INSERT INTO users (spotify_user_id, display_name, email, db_path, 
                             access_token, refresh_token, token_expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (spotify_user_id, display_name, email, db_path, 
              access_token, refresh_token, token_expiry))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return {
            'id': user_id,
            'spotify_user_id': spotify_user_id,
            'display_name': display_name,
            'db_path': db_path
        }
    except sqlite3.IntegrityError:
        # User already exists, update tokens
        cursor.execute("""
            UPDATE users 
            SET access_token = ?, refresh_token = ?, token_expiry = ?,
                display_name = ?, email = ?
            WHERE spotify_user_id = ?
        """, (access_token, refresh_token, token_expiry, 
              display_name, email, spotify_user_id))
        
        conn.commit()
        
        # Get the existing user
        cursor.execute("SELECT * FROM users WHERE spotify_user_id = ?", (spotify_user_id,))
        user = dict(cursor.fetchone())
        conn.close()
        
        return user

def get_user(user_id):
    """Get user by ID"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None

def get_user_by_spotify_id(spotify_user_id):
    """Get user by Spotify user ID"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE spotify_user_id = ?", (spotify_user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None

def get_all_users():
    """Get all users"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return users

def update_user_analysis_status(user_id, status, progress=None):
    """Update user's analysis status and progress"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    cursor = conn.cursor()
    
    if progress is not None:
        cursor.execute("""
            UPDATE users 
            SET analysis_status = ?, analysis_progress = ?
            WHERE id = ?
        """, (status, progress, user_id))
    else:
        cursor.execute("""
            UPDATE users 
            SET analysis_status = ?
            WHERE id = ?
        """, (status, user_id))
    
    conn.commit()
    conn.close()

def delete_user(user_id):
    """Delete a user and their database file"""
    user = get_user(user_id)
    if not user:
        return False
    
    # Delete database file if it exists
    if os.path.exists(user['db_path']):
        os.remove(user['db_path'])
    
    # Delete from master database
    conn = sqlite3.connect(MASTER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return True

def update_user_tokens(user_id, access_token, refresh_token, token_expiry):
    """Update user's OAuth tokens"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET access_token = ?, refresh_token = ?, token_expiry = ?
        WHERE id = ?
    """, (access_token, refresh_token, token_expiry, user_id))
    
    conn.commit()
    conn.close()
def reset_stuck_analyses():
    """Reset all users with 'running' status back to 'pending' on startup"""
    conn = sqlite3.connect(MASTER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET analysis_status = 'pending' WHERE analysis_status = 'running'")
    conn.commit()
    conn.close()
    print("🧹 Reset any stuck analysis statuses")

# Initialize master database on import
if not os.path.exists(MASTER_DB_PATH):
    init_master_db()

# Reset any stuck analyses on startup
reset_stuck_analyses()
