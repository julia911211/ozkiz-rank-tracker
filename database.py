import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DB 설정 (Render - Supabase 연동 대비)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Aggressive cleaning of invisible chars
    DATABASE_URL = "".join(DATABASE_URL.split()) # Remove ALL whitespace/newlines
    
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # URL Encoding for password (if special characters like ! # @ exist)
    if "@" in DATABASE_URL:
        try:
            from urllib.parse import quote_plus
            # Split from the RIGHT to correctly handle '@' in passwords
            # Format: postgresql://user:pass@host:port/db
            prefix, rest = DATABASE_URL.split("://", 1)
            user_info, host_info = rest.rsplit("@", 1) # Find the LAST @
            
            if ":" in user_info:
                user, password = user_info.split(":", 1)
                # Encode the password
                encoded_pass = quote_plus(password)
                DATABASE_URL = f"{prefix}://{user}:{encoded_pass}@{host_info}"
                print(f"DATABASE_URL password encoded. Host: {host_info.split(':')[0]} (Robustly parsed)")
            else:
                print(f"DATABASE_URL host: {host_info.split(':')[0]}")
        except Exception as e:
            print(f"Error robustly parsing/encoding DATABASE_URL: {e}")

if not DATABASE_URL:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "ranking_history.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# PostgreSQL의 경우 및 SQLAlchemy 설정 최적화
connect_args = {}
if DATABASE_URL and "postgresql" in DATABASE_URL:
    # sslmode=require 강제 (Supabase 권장)
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"
    
    # EXTREME TIMEOUT: 60 seconds for cross-region stability (Render to Mumbai)
    connect_args = {
        "connect_timeout": 60,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
    print("PostgreSQL connection args set with EXTREME timeout=60")
elif DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine with robust settings
try:
    engine = create_engine(
        DATABASE_URL, 
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=120,    # Recycle connections faster to avoid stale ones
        pool_size=20,        # Increase pool size for concurrent requests
        max_overflow=30      # Allow more overflow
    )
    print("SQLAlchemy engine created WITH ROBUST SETTINGS.")
except Exception as e:
    print(f"CRITICAL FAILURE creating engine: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RankHistory(Base):
    __tablename__ = "rank_history"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, index=True)
    rank_display = Column(String)  # '1위', '슈퍼적립' 등
    rank_value = Column(Integer)    # 실제 숫자 순위 (비교용)
    product_title = Column(Text)
    product_link = Column(Text)
    product_image = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrackedKeyword(Base):
    __tablename__ = "tracked_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True)
    target_brand = Column(String, default="오즈키즈")
    is_active = Column(Integer, default=1) # 1: 활성, 0: 비활성
    created_at = Column(DateTime, default=datetime.utcnow)

# run_migrations()에서 처리함
# Base.metadata.create_all(bind=engine)

def run_migrations():
    print("Database initialization and migration starting...")
    # 테이블 생성 (스키마 반영)
    try:
        Base.metadata.create_all(bind=engine)
        print("Base.metadata.create_all success")
    except Exception as e:
        print(f"Base.metadata.create_all failed: {e}")

    db = SessionLocal()
    try:
        from sqlalchemy import text
        # Add is_active column if missing
        print("Checking for is_active column...")
        try:
            # Try to select the column to see if it exists
            db.execute(text("SELECT is_active FROM tracked_keywords LIMIT 1"))
            print("'is_active' column already exists.")
        except Exception:
            print("'is_active' column missing, attempting to add...")
            try:
                db.rollback() # Clear failed transaction
                db.execute(text("ALTER TABLE tracked_keywords ADD COLUMN is_active INTEGER DEFAULT 1"))
                db.commit()
                print("Column 'is_active' added successfully.")
            except Exception as e2:
                print(f"Failed to add column: {e2}")
                db.rollback()
    except Exception as e:
        print(f"Migration processing error: {e}")
    finally:
        db.close()

# run_migrations()  # Moved to main.py startup for safety

def save_rank_to_db(keyword: str, rank_display: str, rank_value: int, title: str, link: str, image: str):
    db = SessionLocal()
    try:
        new_entry = RankHistory(
            keyword=keyword,
            rank_display=rank_display,
            rank_value=rank_value,
            product_title=title,
            product_link=link,
            product_image=image
        )
        db.add(new_entry)
        db.commit()
    finally:
        db.close()

def get_latest_rank(keyword: str, title: str):
    db = SessionLocal()
    try:
        result = db.query(RankHistory).filter(
            RankHistory.keyword == keyword,
            RankHistory.product_title == title
        ).order_by(RankHistory.created_at.desc()).first()
        return result
    finally:
        db.close()

def get_all_history():
    db = SessionLocal()
    try:
        results = db.query(RankHistory).order_by(RankHistory.created_at.desc()).all()
        return results
    finally:
        db.close()

# --- 키워드 관리 함수 ---
def get_all_tracked_keywords(include_inactive: bool = False):
    db = SessionLocal()
    try:
        query = db.query(TrackedKeyword)
        if not include_inactive:
            query = query.filter(TrackedKeyword.is_active == 1)
        return query.all()
    finally:
        db.close()

def add_tracked_keyword(keyword: str, target_brand: str = "오즈키즈"):
    db = SessionLocal()
    try:
        existing = db.query(TrackedKeyword).filter(TrackedKeyword.keyword == keyword).first()
        if existing:
            existing.is_active = 1
            existing.target_brand = target_brand
        else:
            new_kw = TrackedKeyword(keyword=keyword, target_brand=target_brand)
            db.add(new_kw)
        db.commit()
    finally:
        db.close()

def remove_tracked_keyword(keyword: str):
    db = SessionLocal()
    try:
        kw = db.query(TrackedKeyword).filter(TrackedKeyword.keyword == keyword).first()
        if kw:
            kw.is_active = 0
            db.commit()
    finally:
        db.close()
