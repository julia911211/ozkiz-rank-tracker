import requests
import urllib.parse
from bs4 import BeautifulSoup
import json
import re

def test_requests():
    keyword = "유치원실내화"
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://search.shopping.naver.com/search/all?query={encoded_kw}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    print(f"[{keyword}] 요청 시작...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"HTTP Error: {response.status_code}")
        return
        
    html = response.text
    
    # 1. 캡차 차단 확인
    if "쇼핑 서비스 접속이 일시적으로 제한되었습니다" in html or "captcha" in html.lower():
        print("경고: 여전히 캡차/차단 페이지가 뜹니다.")
        return
        
    print("정상 로딩 성공! 데이터 분석 시작...")
    
    # html 저장
    with open("req_test.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    # 네이버 쇼핑은 SSR 페이지 로드 시 __NEXT_DATA__ 태그에 JSON으로 초기 데이터를 넣어줍니다. 
    # CSS 파싱보다 안 바뀌고 정확한 방법.
    soup = BeautifulSoup(html, 'html.parser')
    script_tag = soup.find('script', id='__NEXT_DATA__')
    
    if script_tag:
        try:
            data = json.loads(script_tag.string)
            print("NEXT_DATA 파싱 성공! 구조 분석:")
            
            # 여기서 제품 정보 추출 경로를 찾아야 합니다.
            # 보통 props.pageProps.initialState.products.list 등에 위치합니다.
            print(data.keys())
            if 'props' in data:
                print("props keys:", data['props'].keys())
                if 'pageProps' in data['props']:
                    print("pageProps keys:", data['props']['pageProps'].keys())
        except Exception as e:
            print(f"JSON 파싱 에러: {e}")
    else:
        print("__NEXT_DATA__ 스크립트 태그를 찾지 못했습니다. DOM 로직 변경 필요.")

if __name__ == "__main__":
    test_requests()
