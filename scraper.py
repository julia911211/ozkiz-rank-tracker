import os
import urllib.request
import urllib.parse
import json
from dotenv import load_dotenv

load_dotenv()

def get_naver_shopping_rank(keyword: str, target_brand: str = "오즈키즈", super_save_products: list = None):
    # 사용자 발급 API 키 (환경 변수에서 우선 로드)
    client_id = os.getenv("NAVER_CLIENT_ID", "fbL30rvSTNUUBg8PB9av")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "sH4KFgaRnR")
    
    if super_save_products is None:
        super_save_products = []
    
    encoded_kw = urllib.parse.quote(keyword)
    
    # ... (생략) ...
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_kw}&display=40&start=1&sort=sim"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        
        if rescode == 200:
            response_body = response.read()
            data = json.loads(response_body.decode('utf-8'))
            
            items = data.get("items", [])
            parsed_items = []
            
            for idx, item in enumerate(items):
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
                "top_title": final_targets[0]["title"] if final_targets else "검색결과 없음"
            }
        else:
            return {
                "keyword": keyword,
                "status": "error",
                "message": f"API Error Code: {rescode}"
            }
            
    except Exception as e:
        import traceback
        print(f"!!! Error in get_naver_shopping_rank: {str(e)}")
        traceback.print_exc()
        return {
            "keyword": keyword,
            "status": "error",
            "message": f"Server Logic Error: {str(e)}"
        }
