import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from scraper import get_naver_shopping_rank
from database import save_rank_to_db, get_latest_rank, get_all_history

app = FastAPI()


# 절대 경로 설정을 위한 BASE_DIR 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 프론트엔드 정적 파일 서빙 (절대 경로 사용)
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
    # 1. 기존 순위(History) 가져오기 (비교용)
    prev_record = get_latest_rank(req.keyword)
    prev_rank = prev_record.rank_value if prev_record else None
    
    # 2. 현재 순위 스캔
    result = get_naver_shopping_rank(req.keyword, req.target_brand, req.super_save_keywords)
    
    # 3. 결과에 변동폭 계산 추가
    if result["status"] == "success" and result["target_items"]:
        current_item = result["target_items"][0]
        current_rank = current_item["rank"]
        
        # 순위 변동 계산
        if prev_rank is not None:
            diff = prev_rank - current_rank # 예: 3위 -> 1위 = +2 (상승)
            result["rank_diff"] = diff
            result["prev_rank"] = prev_rank
        else:
            result["rank_diff"] = None
            result["prev_rank"] = None
            
        # 4. DB에 현재 결과 저장 (히스토리 누적)
        save_rank_to_db(
            keyword=req.keyword,
            rank_display=current_item["rank_display"],
            rank_value=current_rank,
            title=current_item["title"],
            link=current_item["link"],
            image=current_item["image"]
        )
    
    return result

@app.get("/api/get_history")
def get_history():
    history_data = get_all_history()
    return history_data

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
