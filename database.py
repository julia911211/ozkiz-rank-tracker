import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DB 파일 경로 설정 (Render 기점)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ranking_history.db")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
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

# 테이블 생성
Base.metadata.create_all(bind=engine)

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
def get_all_tracked_keywords():
    db = SessionLocal()
    try:
        return db.query(TrackedKeyword).filter(TrackedKeyword.is_active == 1).all()
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
