import os
import sqlalchemy
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    print("DATABASE_URL not set.")
else:
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check tracked_keywords
            print("Checking tracked_keywords table...")
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='tracked_keywords'"))
            cols = [row[0] for row in res.fetchall()]
            print(f"Columns: {cols}")
            
            if 'is_active' not in cols:
                print("Missing 'is_active' column!")
            else:
                print("'is_active' column exists.")
    except Exception as e:
        print(f"Error checking DB: {e}")
