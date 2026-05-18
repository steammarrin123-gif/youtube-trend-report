import os
from datetime import date, timedelta
from dotenv import load_dotenv
import anthropic

load_dotenv()

BARO_BIRTHDAY = date(2024, 12, 24)
SECOND_DUE_DATE = date(2027, 1, 10)


def _calculate_ages(today=None):
    if today is None:
        today = date.today()

    # 정바로 나이 (개월 + 일)
    months = (today.year - BARO_BIRTHDAY.year) * 12 + (today.month - BARO_BIRTHDAY.month)
    if today.day < BARO_BIRTHDAY.day:
        months -= 1
    days = (today - BARO_BIRTHDAY.replace(year=today.year, month=today.month)).days
    if days < 0:
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days = (today - BARO_BIRTHDAY.replace(year=prev_year, month=prev_month)).days

    # 임신 주차 (예정일 기준 역산 — 임신기간 280일)
    lmp = SECOND_DUE_DATE - timedelta(days=280)
    preg_days = (today - lmp).days
    preg_weeks = preg_days // 7
    preg_day = preg_days % 7
    days_left = (SECOND_DUE_DATE - today).days

    return {
        "baro_months": months,
        "baro_days": days,
        "preg_weeks": preg_weeks,
        "preg_day": preg_day,
        "days_left": days_left,
    }


def generate_daily_message():
    today = date.today()
    ages = _calculate_ages(today)
    date_str = today.strftime("%Y년 %m월 %d일")

    prompt = f"""오늘은 {date_str}이야.

첫째: 정바로 (남아, 생후 {ages['baro_months']}개월 {ages['baro_days']}일)
둘째: 임신 {ages['preg_weeks']}주 {ages['preg_day']}일 (출산예정일 2027년 1월 10일, D-{ages['days_left']}일)

두 아이를 키우는 부모에게 카카오톡으로 보낼 아침 육아 메시지를 작성해줘.
아빠가 엄마와 함께 읽는 메시지야. 따뜻하고 실용적으로, 카카오톡에서 읽기 편하게.

아래 형식을 정확히 따라줘:

☀️ {date_str} 오늘의 육아 정보

👶 정바로 ({ages['baro_months']}개월 {ages['baro_days']}일)
━━━━━━━━━━━━━━━
🧠 이 시기 발달 특징
• [이 월령의 핵심 발달 정보 — 2~3줄, 구체적으로]

💡 오늘의 실천 TIP
• [오늘 바로 해볼 수 있는 활동이나 대화법 1가지]

❤️ 엄마한테 한마디
• [이 시기 육아를 하는 엄마를 위한 따뜻한 응원]

━━━━━━━━━━━━━━━
🤰 둘째 아기 ({ages['preg_weeks']}주 {ages['preg_day']}일, D-{ages['days_left']})
━━━━━━━━━━━━━━━
👶 이번 주 태아 발달
• [현재 주차 태아의 크기/발달 상황 — 구체적으로]

💊 엄마 몸 변화
• [이 주차에 흔한 증상과 대처법]

👨 아빠가 오늘 할 일
• [아빠가 지금 실천할 수 있는 행동 1가지]
━━━━━━━━━━━━━━━

주의사항:
- 의학적으로 정확한 정보만 사용할 것
- 매일 다른 내용이 나오도록 오늘 날짜를 기반으로 다양하게 작성
- 이모지 그대로 유지
- 형식 외 추가 설명 없이 메시지 본문만 출력"""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
