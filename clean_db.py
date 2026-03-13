import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:ozkiz1234!!##@db.kydsitfjogstfmxwynse.supabase.co:5432/postgres'
from database import SessionLocal, RankHistory, TrackedKeyword
db = SessionLocal()
del_hist = db.query(RankHistory).filter(RankHistory.keyword.like('%테스트%')).delete(synchronize_session=False)
del_kw = db.query(TrackedKeyword).filter(TrackedKeyword.keyword.like('%테스트%')).delete(synchronize_session=False)
db.commit()
db.close()
print(f'Deleted {del_hist} history records and {del_kw} keyword records.')
