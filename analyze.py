import sys
from bs4 import BeautifulSoup

def analyze_captcha():
    with open("test_source.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "No Title"
    print(f"PAGE TITLE: {title}")
    
    # 본문 텍스트 일부 추출 (차단 확인용)
    body_text = soup.body.get_text()[:500] if soup.body else "No Body"
    
    # 윈도우 한글 인코딩 에러 방지
    try:
        print(f"BODY PREVIEW:\n{body_text.strip()}")
    except UnicodeEncodeError:
        print(f"BODY PREVIEW (ascii):\n{body_text.strip().encode('ascii', 'replace').decode('ascii')}")

if __name__ == "__main__":
    analyze_captcha()
