import urllib.request
import urllib.parse
import json

def fetch_top_item(keyword):
    client_id = "fbL30rvSTNUUBg8PB9av"
    client_secret = "sH4KFgaRnR"
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_kw}&display=5&start=1&sort=sim"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    response = urllib.request.urlopen(request)
    data = json.loads(response.read().decode('utf-8'))
    return data.get("items", [])[0] if data.get("items") else None

print("Fetching '유치원실내화' (Super Save expected at top)...")
item1 = fetch_top_item("유치원실내화")
print(json.dumps(item1, indent=2, ensure_ascii=False))

print("\nFetching '유아발레슈즈' (Pure organic 1st expected at top)...")
item2 = fetch_top_item("유아발레슈즈")
print(json.dumps(item2, indent=2, ensure_ascii=False))
