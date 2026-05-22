"""
매일 아침 8시 — 카카오톡 메시지 발송 (2개)
- 정바로 육아 정보
- 이예원 건강/마음 정보
"""
import sys
import io
import os
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _is_send_time():
    # GitHub Actions에서 실행되는 경우에만 시간 체크
    if os.environ.get("GITHUB_ACTIONS") == "true":
        now = datetime.now()
        if now.hour == 8 and now.minute < 10:
            return True
        print(f"  발송 시간 아님 (현재: {now.strftime('%H:%M')}). 8시에만 발송합니다.")
        return False
    # 로컬에서 직접 실행할 때는 항상 통과
    return True


def main():
    print(f"\n{'=' * 45}")
    print("  메시지 발송 시작")
    print(f"  실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 45}\n")

    if not _is_send_time():
        return

    print("[1/2] 오늘의 메시지 생성 중...")
    from tools.content_generator import generate_daily_messages
    msg_baro, msg_spouse = generate_daily_messages()
    print("  생성 완료\n")

    from tools.kakao_sender import send_to_me

    print("[2/2] 카카오톡 발송 중...")
    print("  1번 (정바로) 발송...")
    send_to_me(msg_baro)

    print("  2번 (이예원) 발송...")
    send_to_me(msg_spouse)

    print(f"\n{'=' * 45}")
    print("  완료! 카카오톡 2개를 확인해주세요.")
    print(f"{'=' * 45}\n")


if __name__ == "__main__":
    main()
