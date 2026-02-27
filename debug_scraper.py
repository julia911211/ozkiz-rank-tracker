def debug_test():
    from scraper import get_naver_shopping_rank
    result = get_naver_shopping_rank("유치원실내화", "오즈키즈")
    
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Result: {result}\n")

if __name__ == "__main__":
    debug_test()
