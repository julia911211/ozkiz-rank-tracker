import os
import urllib.request
import urllib.parse
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")

def get_naver_shopping_rank(keyword: str, target_brand: str = "오즈키즈", super_save_products: list = None):
    # 사용자 발급 API 키 (환경 변수에서 우선 로드)
    client_id = os.getenv("NAVER_CLIENT_ID", "fbL30rvSTNUUBg8PB9av")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "sH4KFgaRnR")
    
    if super_save_products is None:
        super_save_products = []
    
    encoded_kw = urllib.parse.quote(keyword)
    
    # 네이버 쇼핑 검색 API URL (최대 40개, 유사도순)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_kw}&display=40&start=1&sort=sim"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        logger.info(f"Searching Naver Shopping for: {keyword}")
        response = urllib.request.urlopen(request, timeout=10)
        rescode = response.getcode()
        
        if rescode == 200:
            response_body = response.read()
            data = json.loads(response_body.decode('utf-8'))
            
            items = data.get("items", [])
            parsed_items = []
            
            for idx, item in enumerate(items):
                # HTML 태그 제거 (<b> 등)
                title = item.get("title", "").replace("<b>", "").replace("</b>", "")
                link = item.get("link", "")
                mall = item.get("mallName", "")
                image = item.get("image", "") 
                current_rank = idx + 1
                
                parsed_items.append({
                    "title": title,
                    "link": link,
                    "mall": mall,
                    "image": image,
                    "rank": current_rank
                })
            
            target_list = []
            target_brand = target_brand.strip()
            
            for item in parsed_items:
                # 대소문자 구분 없이 브랜드명 체크
                title_match = target_brand.lower() in item["title"].lower()
                mall_match = target_brand.lower() in item["mall"].lower()
                
                if title_match or mall_match:
                    target_list.append(item)
            
            # 상위 5개 추출 및 슈퍼적립 보정
            final_targets = target_list[:5]
            
            for item in final_targets:
                is_super_save = False
                for kw_match in super_save_products:
                    if kw_match and kw_match.lower() in item["title"].lower():
                        is_super_save = True
                        break
                
                if is_super_save:
                    item["rank_display"] = "슈퍼적립"
                else:
                    item["rank_display"] = f"{item['rank']}위"
            
            return {
                "keyword": keyword,
                "status": "success",
                "total_items_found": len(parsed_items),
                "target_items": final_targets,
                "top_rank": final_targets[0]["rank_display"] if final_targets else "-",
                "top_title": final_targets[0]["title"] if final_targets else "40위 내 검색결과 없음"
            }
        else:
            return {
                "keyword": keyword,
                "status": "error",
                "message": f"네이버 API 응답 오류 (코드: {rescode})"
            }
            
    except urllib.error.HTTPError as e:
        if e.code == 429:
            msg = "네이버 API 호출 한도 초과 (잠시 후 다시 시도해주세요)"
        elif e.code == 401 or e.code == 403:
            msg = "네이버 API 인증 실패 (Client ID/Secret 확인 필요)"
        else:
            msg = f"HTTP 오류 발생 (코드: {e.code})"
        return {"keyword": keyword, "status": "error", "message": msg}
        
    except Exception as e:
        import traceback
        logger.error(f"Error in get_naver_shopping_rank: {str(e)}")
        traceback.print_exc()
        return {
            "keyword": keyword,
            "status": "error",
            "message": f"시스템 로직 오류: {str(e)}"
        }
