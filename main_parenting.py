"""
매일 아침 8시 — 육아 카카오톡 메시지 발송 (2개)
"""
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def main():
    print(f"\n{'=' * 45}")
    print("  육아 메시지 발송 시작")
    print(f"  실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 45}\n")

    # 1. 메시지 2개 생성
    print("[1/2] 오늘의 육아 메시지 생성 중...")
    from tools.content_generator import generate_daily_messages
    msg1, msg2 = generate_daily_messages()
    print("  생성 완료\n")

    # 2. 카카오톡 2번 발송
    from tools.kakao_sender import send_to_me

    print("[2/2] 카카오톡 발송 중...")
    print("  1번 메시지 (날씨 + 정바로) 발송...")
    send_to_me(msg1)

    print("  2번 메시지 (왕눈이) 발송...")
    send_to_me(msg2)

    print(f"\n{'=' * 45}")
    print("  완료! 카카오톡 2개를 확인해주세요.")
    print(f"{'=' * 45}\n")


if __name__ == "__main__":
    main()
