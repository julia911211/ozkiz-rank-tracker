import time
from playwright.sync_api import sync_playwright

def screenshot_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--window-position=0,0',
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.new_page()
        page.goto("https://search.shopping.naver.com/search/all?query=유치원실내화", wait_until="networkidle")
        
        print("페이지 로딩 대기중...")
        time.sleep(5)
        
        print("스크린샷 저장중...")
        page.screenshot(path="naver_test.png", full_page=True)
        
        print("HTML 소스 저장중...")
        with open("test_source2.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        browser.close()

if __name__ == "__main__":
    screenshot_test()
