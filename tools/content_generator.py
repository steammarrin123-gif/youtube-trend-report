import os
import json
import urllib.request
from datetime import date, timedelta
from dotenv import load_dotenv
import anthropic

load_dotenv()

BARO_BIRTHDAY = date(2024, 12, 24)
SECOND_DUE_DATE = date(2027, 1, 10)

KHOA_OBS_CODES = {
    "광양": "DT_0056",
    "여수": "DT_0059",
}


def _calculate_ages(today=None):
    if today is None:
        today = date.today()

    months = (today.year - BARO_BIRTHDAY.year) * 12 + (today.month - BARO_BIRTHDAY.month)
    if today.day < BARO_BIRTHDAY.day:
        months -= 1
    days = (today - BARO_BIRTHDAY.replace(year=today.year, month=today.month)).days
    if days < 0:
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days = (today - BARO_BIRTHDAY.replace(year=prev_year, month=prev_month)).days

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


def _fetch_wttr(city_en):
    try:
        url = f"https://wttr.in/{city_en}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read())
    except Exception:
        return None


def _get_weather_suncheon():
    data = _fetch_wttr("Suncheon")
    if not data:
        return "날씨 정보를 가져올 수 없습니다."

    current = data["current_condition"][0]
    temp = current["temp_C"]
    feels_like = current["FeelsLikeC"]
    humidity = current["humidity"]
    desc_list = current.get("lang_ko", [])
    desc = desc_list[0]["value"] if desc_list else current["weatherDesc"][0]["value"]

    today_w = data["weather"][0]
    max_temp = today_w["maxtempC"]
    min_temp = today_w["mintempC"]

    return (
        f"현재 {temp}°C (체감 {feels_like}°C), 습도 {humidity}%\n"
        f"최고 {max_temp}°C / 최저 {min_temp}°C, {desc}"
    )


def _get_marine_info(city_en):
    data = _fetch_wttr(city_en)
    if not data:
        return None

    current = data["current_condition"][0]
    wind_kmph = int(current.get("windspeedKmph", 0))
    wind_ms = round(wind_kmph / 3.6, 1)
    precip = float(current.get("precipMM", 0))
    rain = "있음" if precip > 0 else "없음"

    wave_height = "정보없음"
    for hour in data["weather"][0].get("hourly", []):
        sig = hour.get("sigHeight_m")
        if sig:
            wave_height = f"{sig}m"
            break

    return {"rain": rain, "wind_ms": wind_ms, "wave": wave_height}


def _get_tide_info(city_kr):
    khoa_key = os.getenv("KHOA_API_KEY")
    if not khoa_key:
        return None

    obs_code = KHOA_OBS_CODES.get(city_kr)
    if not obs_code:
        return None

    today = date.today().strftime("%Y%m%d")
    url = (
        f"http://www.khoa.go.kr/api/oceangrid/tidalBul/search.do"
        f"?ServiceKey={khoa_key}&ObsCode={obs_code}&Date={today}&ResultType=json"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read())

        items = data.get("result", {}).get("data", [])
        highs = [f"{x['tph_time']}({x['tph_level']}cm)" for x in items if x.get("hl_code") == "H"]
        lows = [f"{x['tph_time']}({x['tph_level']}cm)" for x in items if x.get("hl_code") == "L"]

        return {
            "고조": " / ".join(highs) if highs else "정보없음",
            "저조": " / ".join(lows) if lows else "정보없음",
        }
    except Exception:
        return None


def _format_marine_section(city_kr, city_en):
    marine = _get_marine_info(city_en)
    tide = _get_tide_info(city_kr)

    lines = [f"⚓ {city_kr}"]
    if marine:
        lines.append(f"비: {marine['rain']} | 바람: {marine['wind_ms']}m/s | 파도: {marine['wave']}")
    else:
        lines.append("해양 정보를 가져올 수 없습니다.")

    if tide:
        lines.append(f"고조: {tide['고조']}")
        lines.append(f"저조: {tide['저조']}")
    else:
        lines.append("조석: API 키 미설정 (KHOA_API_KEY 필요)")

    return "\n".join(lines)


def generate_daily_message():
    today = date.today()
    ages = _calculate_ages(today)
    date_str = today.strftime("%Y년 %m월 %d일")
    weather_suncheon = _get_weather_suncheon()
    gwangyang_section = _format_marine_section("광양", "Gwangyang")
    yeosu_section = _format_marine_section("여수", "Yeosu")

    weather_block = (
        f"🌤️ 순천\n{weather_suncheon}\n\n"
        f"{gwangyang_section}\n\n"
        f"{yeosu_section}"
    )

    prompt = f"""오늘은 {date_str}이야.

[날씨 / 해양 정보]
{weather_block}

첫째: 정바로 (남아, 생후 {ages['baro_months']}개월 {ages['baro_days']}일)
둘째: 왕눈이 (임신 {ages['preg_weeks']}주 {ages['preg_day']}일, 출산예정일 2027년 1월 10일, D-{ages['days_left']}일)

두 아이를 키우는 부모에게 카카오톡으로 보낼 아침 육아 메시지를 작성해줘.
아빠가 엄마와 함께 읽는 메시지야. 따뜻하고 실용적으로, 카카오톡에서 읽기 편하게.
각 항목마다 충분히 자세하게 써줘. 짧게 쓰지 말고, 읽으면서 도움이 되는 구체적인 내용으로 채워줘.

아래 형식을 정확히 따라줘:

☀️ {date_str} 오늘의 육아 정보

🌤️ 날씨 / 해양 정보
━━━━━━━━━━━━━━━
{weather_block}

👶 정바로 ({ages['baro_months']}개월 {ages['baro_days']}일)
━━━━━━━━━━━━━━━
🧠 이 시기 발달 특징
• [이 월령의 핵심 발달 정보 — 3~4줄, 아주 구체적으로]

💡 오늘의 실천 TIP
• [오늘 바로 해볼 수 있는 활동이나 대화법 — 2~3가지, 각각 한 줄씩]

🍽️ 이 시기 식습관
• [이 월령에 맞는 식사 팁이나 주의할 음식 — 2줄]

❤️ 엄마한테 한마디
• [이 시기 육아를 하는 엄마를 위한 따뜻한 응원 — 3~4줄, 진심 담아서]

━━━━━━━━━━━━━━━
🤰 왕눈이 ({ages['preg_weeks']}주 {ages['preg_day']}일, D-{ages['days_left']})
━━━━━━━━━━━━━━━
👶 이번 주 태아 발달
• [현재 주차 태아의 크기/발달 상황 — 3~4줄, 구체적으로]

💊 엄마 몸 변화
• [이 주차에 흔한 증상과 대처법 — 3줄, 실용적인 팁 포함]

🥗 이번 주 추천 음식
• [이 임신 주차에 특히 좋은 음식 2~3가지와 이유]

👨 아빠가 오늘 할 일
• [아빠가 지금 실천할 수 있는 행동 2~3가지]

💬 오늘의 태담
• [왕눈이에게 말 걸어줄 수 있는 따뜻한 태담 한 문장]
━━━━━━━━━━━━━━━

주의사항:
- 의학적으로 정확한 정보만 사용할 것
- 매일 다른 내용이 나오도록 오늘 날짜를 기반으로 다양하게 작성
- 이모지 그대로 유지
- 형식 외 추가 설명 없이 메시지 본문만 출력"""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
