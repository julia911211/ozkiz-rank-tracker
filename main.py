import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from scraper import get_naver_shopping_rank

app = FastAPI()

# 프론트엔드 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

class SingleSearchRequest(BaseModel):
    keyword: str
    target_brand: str
    super_save_keywords: list[str] = []

@app.post("/api/search_single")
def search_single(req: SingleSearchRequest):
    result = get_naver_shopping_rank(req.keyword, req.target_brand, req.super_save_keywords)
    return result

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
