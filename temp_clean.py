import sqlite3
try:
    conn = sqlite3.connect('ranking_history.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM rank_history WHERE keyword LIKE '%테스트%'")
    cur.execute("DELETE FROM tracked_keywords WHERE keyword LIKE '%테스트%'")
    conn.commit()
    print(f"Cleanup done: {cur.rowcount} rows affected.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
