import uvicorn
from pyngrok import ngrok
from main import app
import os

def launch():
    # ngrok 터널 열기 (포트 8000)
    # 별도의 auth token 없이도 실행 가능하지만, 가끔 제한이 있을 수 있습니다.
    try:
        public_url = ngrok.connect(8000).public_url
        with open("ngrok_url.txt", "w") as f:
            f.write(public_url)
        print("\n" + "="*50)
        print("Success: External Access URL Created!")
        print(f"URL: {public_url}")
        print("Share this URL with your colleagues for external access.")
        print("="*50 + "\n")
    except Exception as e:
        print(f"ngrok 연결 중 오류 발생: {e}")
        print("서버는 로컬(localhost:8000)에서만 실행됩니다.")

    # uvicorn 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    launch()
