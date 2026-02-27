import sys
from scraper import get_naver_shopping_rank

def test_scraper():
    keyword = "유치원실내화"
    print(f"[{keyword}] 테스트 시작...")
    
    result = get_naver_shopping_rank(keyword, "오즈키즈")
    
    print("\n--- 결과 ---")
    print(result)

if __name__ == "__main__":
    test_scraper()
