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
    # 3. 결과 처리 및 모든 상품 DB 저장
    if result["status"] == "success":
        for item in result.get("target_items", []):
            # 각 상품별 기존 순위 가져오기
            prev_record = get_latest_rank(req.keyword, item["title"])
            prev_rank = prev_record.rank_value if prev_record else None
            
            # 현재 순위와 비교
            current_rank = item["rank"]
            rank_diff = None
            if prev_rank is not None:
                rank_diff = prev_rank - current_rank
            
            # 상품 객체에 정보 추가 (프론트 표시용 - 첫번째 아이템 중심일 수 있으나 일단 모두 계산)
            item["rank_diff"] = rank_diff
            item["prev_rank"] = prev_rank
            
            # DB 저장
            save_rank_to_db(
                keyword=req.keyword,
                rank_display=item["rank_display"],
                rank_value=current_rank,
                title=item["title"],
                link=item["link"],
                image=item["image"]
            )
            
        # 프론트엔드 호환성을 위해 상위 1개 정보 result 루트에 유지
        if result["target_items"]:
            result["rank_diff"] = result["target_items"][0].get("rank_diff")
            result["prev_rank"] = result["target_items"][0].get("prev_rank")
    
    return result

@app.get("/api/get_history_grid")
def get_history_grid():
    history = get_all_history()
    
    # 1. 모든 고유 날짜 추출 (YYYY-MM-DD 형식) 및 정렬
    dates = sorted(list(set(h.created_at.strftime("%Y-%m-%d") for h in history)), reverse=True)
    
    # 2. 데이터를 { (키워드, 상품명): { 날짜: 순위정보 } } 형태로 그룹화
    grid_data = {}
    for h in history:
        key = (h.keyword, h.product_title, h.product_image, h.product_link)
        if key not in grid_data:
            grid_data[key] = {}
        
        date_str = h.created_at.strftime("%Y-%m-%d")
        # 해당 날짜의 첫 번째(또는 최신) 기록만 유지
        if date_str not in grid_data[key]:
            grid_data[key][date_str] = {
                "rank_display": h.rank_display,
                "rank_value": h.rank_value,
                "created_at": h.created_at.isoformat()
            }
            
    # 3. 프론트엔드용 포맷으로 변환
    rows = []
    for key, history_map in grid_data.items():
        keyword, title, image, link = key
        
        # 날짜별 등락 계산 (이전 날짜 데이터 찾기)
        history_list = []
        for i, date in enumerate(dates):
            current = history_map.get(date)
            diff = None
            is_new = False
            
            if current:
                # 다음(과거) 날짜 데이터와 비교
                next_date = None
                for d in dates[i+1:]:
                    if d in history_map:
                        next_date = d
                        break
                
                if next_date:
                    prev = history_map[next_date]
                    diff = prev["rank_value"] - current["rank_value"]
                else:
                    is_new = True # 이전 기록이 없으면 NEW
                    
                history_list.append({
                    "date": date,
                    "rank": current["rank_display"],
                    "diff": diff,
                    "is_new": is_new
                })
            else:
                history_list.append({
                    "date": date,
                    "rank": "-",
                    "diff": None,
                    "is_new": False
                })
                
        rows.append({
            "keyword": keyword,
            "title": title,
            "image": image,
            "link": link,
            "history": history_list
        })
        
    return {
        "dates": dates,
        "rows": rows
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
