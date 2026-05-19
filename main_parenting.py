"""
매일 아침 8시 — 육아 카카오톡 메시지 발송 (4개)
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

    print("[1/2] 오늘의 메시지 생성 중...")
    from tools.content_generator import generate_daily_messages
    msg_weather, msg_baro, msg_wangnuni, msg_boat = generate_daily_messages()
    print("  생성 완료\n")

    from tools.kakao_sender import send_to_me

    print("[2/2] 카카오톡 발송 중...")
    print("  1번 (날씨) 발송...")
    send_to_me(msg_weather)

    print("  2번 (정바로) 발송...")
    send_to_me(msg_baro)

    print("  3번 (왕눈이) 발송...")
    send_to_me(msg_wangnuni)

    print("  4번 (배 둘러보기) 발송...")
    send_to_me(msg_boat)

    print(f"\n{'=' * 45}")
    print("  완료! 카카오톡 4개를 확인해주세요.")
    print(f"{'=' * 45}\n")


if __name__ == "__main__":
    main()
