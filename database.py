import os
import re
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url

# --- DB 설정 (Robust Reconstruction) ---
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        # 1. Basic cleanup
        url_str = DATABASE_URL.strip().replace("postgres://", "postgresql://", 1)
        
        # 2. Case-insensitive pgbouncer stripping
        url_str = re.sub(r'([?&])pgbouncer=[^&]*(&|$)', r'\1', url_str, flags=re.IGNORECASE)
        url_str = url_str.rstrip('?&').replace("?&", "?")
        
        # 3. SQLAlchemy URL Parsing
        u = make_url(url_str)
        
        # 4. Supabase Pooler Port Handling (Force Transaction Mode 6543)
        if u.host and "pooler.supabase.com" in u.host:
            u = u.set(port=6543)
            print(f"FORCED SUPABASE POOLER PORT: 6543 for host {u.host}")
            
        # 5. SSL Enforcement (psycopg2 style inside query OR connect_args)
        # We'll put it in query and also in connect_args for double safety
        query = dict(u.query)
        query["sslmode"] = "require"
        u = u.set(query=query)
        
        DATABASE_URL = str(u)
        print(f"DATABASE_URL successfully rebuilt and sanitized.")
    except Exception as e:
        print(f"Error robustly parsing/rebuilding DATABASE_URL: {e}")
        # Very simple fallback if all else fails
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "ranking_history.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# PostgreSQL-specific connection optimization
connect_args = {}
if DATABASE_URL and "postgresql" in DATABASE_URL:
    # sslmode will be handled in connect_args below
    
    # 30s timeout is more reasonable for cross-region
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 30, 
        "keepalives": 1,
        "keepalives_idle": 20,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        "options": "-c idle_in_transaction_session_timeout=30000" # 30s
    }
    print("PostgreSQL connection args set with FAST FAIL timeout=10s")
elif DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine with robust settings for Render/Supabase environment
try:
    engine = create_engine(
        DATABASE_URL, 
        connect_args=connect_args,
        pool_pre_ping=True,      # Check connection validity before using
        pool_recycle=45,         # Even faster recycle
        pool_size=5,             # REDUCED: Don't overwhelm the remote pooler
        max_overflow=8,          # Allow some burst but keep it tight
        pool_timeout=60          # Wait longer for a pool connection from the pool
    )
    print(f"SQLAlchemy engine created WITH ULTIMATE SETTINGS (Pool: 5/8).")
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

def retry_on_db_error(retries=3, delay=2):
    """Decorator to retry database operations on transient connection errors."""
    import time
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            last_err = None
            for i in range(retries):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    # Check for timeout or connection errors
                    err_str = str(e).lower()
                    if "timeout" in err_str or "connection" in err_str or "operationalerror" in err_str:
                        print(f"DB Error (Attempt {i+1}/{retries}): {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    raise # Non-transient error
            print(f"DB operation failed after {retries} attempts.")
            raise last_err
        return wrapper
    return decorator

# apply retry to migrations if needed
# Reduced retries for Render startup safety
@retry_on_db_error(retries=2, delay=2)
def run_migrations():
    print("Database initialization and migration starting...")
    # 테이블 생성 (스키마 반영)
    try:
        Base.metadata.create_all(bind=engine)
        print("Base.metadata.create_all success")
    except Exception as e:
        print(f"Base.metadata.create_all failed: {e}")
        raise # important for retry

# run_migrations()  # Moved to main.py startup for safety

def save_rank_to_db(keyword: str, rank_display: str, rank_value: int, title: str, link: str, image: str):
    """Saves a single rank record to the database."""
    items = [{
        "keyword": keyword,
        "rank_display": rank_display,
        "rank_value": rank_value,
        "title": title,
        "link": link,
        "image": image
    }]
    save_ranks_to_db(items)

@retry_on_db_error(retries=3, delay=2)
def save_ranks_to_db(items: list):
    """
    Saves multiple rank records to the database in a single transaction.
    Expected item structure: {'keyword', 'rank_display', 'rank_value', 'title', 'link', 'image'}
    """
    if not items:
        return
        
    db = SessionLocal()
    try:
        new_entries = []
        for item in items:
            new_entry = RankHistory(
                keyword=item["keyword"],
                rank_display=item["rank_display"],
                rank_value=item["rank_value"],
                product_title=item["title"],
                product_link=item["link"],
                product_image=item["image"]
            )
            new_entries.append(new_entry)
        
        db.add_all(new_entries)
        db.commit()
    except Exception as e:
        print(f"Database bulk save error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@retry_on_db_error(retries=3, delay=1)
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

@retry_on_db_error(retries=3, delay=1)
def get_all_history():
    db = SessionLocal()
    try:
        results = db.query(RankHistory).order_by(RankHistory.created_at.desc()).all()
        return results
    finally:
        db.close()

# --- 키워드 관리 함수 ---
@retry_on_db_error(retries=3, delay=1)
def get_all_tracked_keywords(include_inactive: bool = False):
    db = SessionLocal()
    try:
        query = db.query(TrackedKeyword)
        if not include_inactive:
            query = query.filter(TrackedKeyword.is_active == 1)
        return query.all()
    finally:
        db.close()

@retry_on_db_error(retries=3, delay=2)
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

@retry_on_db_error(retries=3, delay=2)
def remove_tracked_keyword(keyword: str):
    db = SessionLocal()
    try:
        kw = db.query(TrackedKeyword).filter(TrackedKeyword.keyword == keyword).first()
        if kw:
            kw.is_active = 0
            db.commit()
    finally:
        db.close()
