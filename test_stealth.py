import time
from playwright.sync_api import sync_playwright

def advanced_stealth():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '--window-position=-32000,-32000',
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            java_script_enabled=True,
            bypass_csp=True,
            extra_http_headers={
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        # 스텔스 패키지 적용
        try:
            from playwright_stealth import stealth_sync
        except ImportError:
            stealth_sync = None

        page = context.new_page()
        
        # Webdriver 플래그 직접 삭제
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {}
            };
        """)
        
        if stealth_sync:
            stealth_sync(page)

        print("[유치원실내화] 접근 시도...")
        page.goto("https://search.shopping.naver.com/search/all?query=유치원실내화", wait_until="networkidle")
        
        time.sleep(3)
        html = page.content()
        title = page.title()
        print(f"로드된 타이틀: {title}")
        
        # 차단 텍스트 검출
        if "쇼핑 서비스 접속이 일시적으로 제한되었습니다" in html:
            print("❌ 우회 실패. 여전히 차단 페이지입니다.")
        else:
            print("✅ 우회 성공! 일반 페이지 로딩됨.")
            with open("test_source_success.html", "w", encoding="utf-8") as f:
                f.write(html)
            
        browser.close()

if __name__ == "__main__":
    advanced_stealth()
