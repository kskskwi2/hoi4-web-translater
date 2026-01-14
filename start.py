import uvicorn
import webbrowser
import os
import sys
import threading
import time


def open_browser():
    """Wait for server to start then open browser"""
    time.sleep(1.5)
    print("브라우저를 실행합니다: http://localhost:8080 ...")
    webbrowser.open("http://localhost:8080")


def main():
    print("==================================================")
    print("       HOI4 웹 번역기 서버를 시작합니다")
    print("==================================================")

    # Check if frontend build exists
    frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
    if os.path.exists(frontend_dist):
        print(f"[확인] 프론트엔드 빌드 발견: {frontend_dist}")
        print("[모드] 프로덕션 모드 (백엔드 + 프론트엔드 통합 실행)")
    else:
        print("[경고] 프론트엔드 빌드를 찾을 수 없습니다.")
        print(
            "       API 전용 모드로 실행됩니다. 웹 화면을 보려면 'npm run build'가 필요합니다."
        )

    # Schedule browser open
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Server
    print("[시작] 서버 구동 중... (Ctrl+C로 종료)")
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8080,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
