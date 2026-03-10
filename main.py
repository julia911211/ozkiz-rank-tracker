import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from scraper import get_naver_shopping_rank
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from database import (
    save_rank_to_db, get_latest_rank, get_all_history, 
    get_all_tracked_keywords, add_tracked_keyword, remove_tracked_keyword
)

app = FastAPI()

# --- 자동 스케줄러 및 크론 API ---
def daily_ranking_scan():
    print(f"[{datetime.now()}] 자동 데일리 스캔 시작...")
    keywords = get_all_tracked_keywords()
    if not keywords:
        print(" > 등록된 마스터 키워드가 없습니다.")
        return
        
    for kw_obj in keywords:
        try:
            print(f" > '{kw_obj.keyword}' 자동 검색 중...")
            # 마스터 목록 저장 시 저장했던 target_brand 사용
            result = get_naver_shopping_rank(kw_obj.keyword, kw_obj.target_brand, [])
            
            if result["status"] == "success":
                for item in result.get("target_items", []):
                    save_rank_to_db(
                        keyword=kw_obj.keyword,
                        rank_display=item["rank_display"],
                        rank_value=item["rank"],
                        title=item["title"],
                        link=item["link"],
                        image=item["image"]
                    )
            # 네이버 차단 방지를 위한 짧은 휴식
            import time
            time.sleep(2)
        except Exception as e:
            print(f" !!! '{kw_obj.keyword}' 자동 검색 실패: {str(e)}")
    print(f"[{datetime.now()}] 자동 데일리 스캔 완료.")

# 외부에서 호출 가능한 크론 전용 엔드포인트
@app.get("/api/cron/scan")
def cron_scan(key: str = None):
    # 간단한 보안을 위해 환경변수에 설정된 CRON_SECRET 확인
    secret = os.getenv("CRON_SECRET", "ozkiz_default_secret")
    if key != secret:
        return {"status": "error", "message": "Unauthorized"}
        
    # 백그라운드 태스크로 실행 (API 응답은 즉시 반환)
    from fastapi import BackgroundTasks
    def run_and_log():
        daily_ranking_scan()
        
    return {"status": "success", "message": "Scan started in background"}

scheduler = BackgroundScheduler()
# 내부 스케줄러 (서버가 깨어있을 때의 백업용)
scheduler.add_job(daily_ranking_scan, 'cron', hour=2, minute=0)
scheduler.start()

# --- 앱 시작 시 자가 진단 및 초기화 ---
@app.on_event("startup")
async def startup_event():
    print("서버 시작 및 스케줄러 가동 확인...")

# 절대 경로 설정을 위한 BASE_DIR 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 프론트엔드 정적 파일 서빙
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)

class SingleSearchRequest(BaseModel):
    keyword: str
    target_brand: str
    super_save_keywords: list[str] = []

@app.post("/api/search_single")
def search_single(req: SingleSearchRequest):
    result = get_naver_shopping_rank(req.keyword, req.target_brand, req.super_save_keywords)
    
    if result["status"] == "success":
        for item in result.get("target_items", []):
            prev_record = get_latest_rank(req.keyword, item["title"])
            prev_rank = prev_record.rank_value if prev_record else None
            
            current_rank = item["rank"]
            rank_diff = None
            if prev_rank is not None:
                rank_diff = prev_rank - current_rank
            
            item["rank_diff"] = rank_diff
            item["prev_rank"] = prev_rank
            
            save_rank_to_db(
                keyword=req.keyword,
                rank_display=item["rank_display"],
                rank_value=current_rank,
                title=item["title"],
                link=item["link"],
                image=item["image"]
            )
            
        if result.get("target_items"):
            result["rank_diff"] = result["target_items"][0].get("rank_diff")
            result["prev_rank"] = result["target_items"][0].get("prev_rank")
    
    return result

@app.get("/api/get_history_grid")
def get_history_grid():
    history = get_all_history()
    dates = sorted(list(set(h.created_at.strftime("%Y-%m-%d") for h in history)), reverse=True)
    
    grid_data = {}
    for h in history:
        key = (h.keyword, h.product_title, h.product_image, h.product_link)
        if key not in grid_data:
            grid_data[key] = {}
        
        date_str = h.created_at.strftime("%Y-%m-%d")
        if date_str not in grid_data[key]:
            grid_data[key][date_str] = {
                "rank_display": h.rank_display,
                "rank_value": h.rank_value,
                "created_at": h.created_at.isoformat()
            }
            
    # Include tracked keywords that have no history yet
    kws = get_all_tracked_keywords()
    for kw in kws:
        exists = any(key[0] == kw.keyword for key in grid_data.keys())
        if not exists:
            dummy_key = (kw.keyword, "-", "", "")
            grid_data[dummy_key] = {}
            
    rows = []
    for key, history_map in grid_data.items():
        keyword, title, image, link = key
        history_list = []
        for i, date in enumerate(dates):
            current = history_map.get(date)
            diff = None
            is_new = False
            
            if current:
                next_date = None
                for d in dates[i+1:]:
                    if d in history_map:
                        next_date = d
                        break
                
                if next_date:
                    prev = history_map[next_date]
                    diff = prev["rank_value"] - current["rank_value"]
                else:
                    is_new = True
                
                history_list.append({
                    "date": date, "rank": current["rank_display"], "diff": diff, "is_new": is_new
                })
            else:
                history_list.append({
                    "date": date, "rank": "-", "diff": None, "is_new": False
                })
                
        rows.append({
            "keyword": keyword, "title": title, "image": image, "link": link, "history": history_list
        })
        
    return {"dates": dates, "rows": rows}

@app.get("/api/keywords")
def get_keywords():
    kws = get_all_tracked_keywords()
    return [{"id": k.id, "keyword": k.keyword} for k in kws]

@app.post("/api/keywords")
def update_keywords(req: dict):
    new_keywords = req.get("keywords", [])
    target_brand = req.get("target_brand", "오즈키즈")
    
    current_kws = get_all_tracked_keywords()
    for ck in current_kws:
        remove_tracked_keyword(ck.keyword)
        
    for nk in new_keywords:
        if nk.strip():
            add_tracked_keyword(nk.strip(), target_brand)
            
    return {"status": "success", "count": len(new_keywords)}

@app.get("/api/ping")
def ping():
    return {"status": "alive", "time": datetime.now().isoformat()}

@app.get("/api/clean_tests")
def clean_tests():
    try:
        db = SessionLocal()
        del_hist = db.query(RankHistory).filter(RankHistory.keyword.like('%테스트%')).delete(synchronize_session=False)
        del_kw = db.query(TrackedKeyword).filter(TrackedKeyword.keyword.like('%테스트%')).delete(synchronize_session=False)
        db.commit()
        db.close()
        return {"deleted_history": del_hist, "deleted_keywords": del_kw}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
