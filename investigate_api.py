import urllib.request
import urllib.parse
import json

def investigate():
    keyword = "유치원실내화"
    client_id = "fbL30rvSTNUUBg8PB9av"
    client_secret = "sH4KFgaRnR"
    
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_kw}&display=40&start=1&sort=sim"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode('utf-8'))
        items = data.get("items", [])
        
        with open("api_items_dump.txt", "w", encoding="utf-8") as f:
            f.write(f"Keyword: {keyword}\n")
            for idx, item in enumerate(items):
                title = item.get("title", "").replace("<b>", "").replace("</b>", "")
                mall = item.get("mallName", "")
                f.write(f"{idx+1}. [{mall}] {title}\n")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    investigate()
