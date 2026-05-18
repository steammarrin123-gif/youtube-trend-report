"""
매일 아침 8시 — 육아 카카오톡 메시지 발송
"""
import sys
import io
from datetime import datetime

# 터미널 인코딩 문제 방지 (이모지 출력 시 cp949 오류 해결)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def main():
    print(f"\n{'=' * 45}")
    print("  육아 메시지 발송 시작")
    print(f"  실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 45}\n")

    # 1. 메시지 생성 (Claude API)
    print("[1/2] 오늘의 육아 메시지 생성 중...")
    from tools.content_generator import generate_daily_message
    message = generate_daily_message()
    print("  생성 완료\n")
    print("─" * 40)
    print(message)
    print("─" * 40 + "\n")

    # 2. 카카오톡 발송
    print("[2/2] 카카오톡 발송 중...")
    from tools.kakao_sender import send_to_me
    send_to_me(message)

    print(f"\n{'=' * 45}")
    print("  완료! 카카오톡을 확인해주세요.")
    print(f"{'=' * 45}\n")


if __name__ == "__main__":
    main()
