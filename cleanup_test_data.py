import sqlite3
import os

# Try to find the SQLite DB
db_path = 'ranking_history.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    if 'rank_history' in tables:
        cursor.execute("DELETE FROM rank_history WHERE keyword LIKE '%테스트%'")
        print(f"Deleted from rank_history: {cursor.rowcount} rows")
        
    if 'tracked_keywords' in tables:
        cursor.execute("DELETE FROM tracked_keywords WHERE keyword LIKE '%테스트%'")
        print(f"Deleted from tracked_keywords: {cursor.rowcount} rows")
        
    conn.commit()
    conn.close()
    print("Cleanup complete.")
else:
    print(f"{db_path} not found.")
