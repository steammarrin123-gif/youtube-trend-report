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


def generate_daily_messages():
    today = date.today()
    ages = _calculate_ages(today)
    date_str = today.strftime("%Y년 %m월 %d일")
    weather_suncheon = _get_weather_suncheon()
    gwangyang_section = _format_marine_section("광양", "Gwangyang")
    yeosu_section = _format_marine_section("여수", "Yeosu")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def city_weather(city_en):
        d = _fetch_wttr(city_en)
        if not d:
            return None
        cur = d["current_condition"][0]
        temp = cur["temp_C"]
        precip = float(cur.get("precipMM", 0))
        rain = "비 있음 🌧️" if precip > 0 else "맑음 ☀️"
        max_t = d["weather"][0]["maxtempC"]
        min_t = d["weather"][0]["mintempC"]
        return {"temp": temp, "rain": rain, "max": max_t, "min": min_t}

    sc = city_weather("Suncheon")
    gw = city_weather("Gwangyang")
    ys = city_weather("Yeosu")

    weather_raw = (
        f"순천: 현재 {sc['temp']}°C (최고 {sc['max']}°C / 최저 {sc['min']}°C), {sc['rain']}\n"
        f"광양: 현재 {gw['temp']}°C (최고 {gw['max']}°C / 최저 {gw['min']}°C), {gw['rain']}\n"
        f"여수: 현재 {ys['temp']}°C (최고 {ys['max']}°C / 최저 {ys['min']}°C), {ys['rain']}"
    ) if sc and gw and ys else "날씨 정보를 가져올 수 없습니다."

    prompt_baro = f"""오늘은 {date_str}이야.
첫째: 정바로 (남아, 생후 {ages['baro_months']}개월 {ages['baro_days']}일)

아래 형식을 정확히 따라줘. 각 항목 3~4줄로 자세하게 써줘:

👶 정바로 ({ages['baro_months']}개월 {ages['baro_days']}일)
━━━━━━━━━━━━━━━
🧠 이 시기 발달 특징
• [이 월령의 핵심 발달 정보 — 3~4줄, 구체적으로]

💡 오늘의 실천 TIP
• [오늘 바로 해볼 수 있는 활동 2~3가지]

🍽️ 이 시기 식습관
• [식사 팁이나 주의할 음식 — 2줄]

❤️ 엄마한테 한마디
• [따뜻한 응원 — 3~4줄]
━━━━━━━━━━━━━━━

주의사항: 의학적으로 정확한 정보만. 이모지 유지. 본문만 출력."""

    prompt_spouse = f"""오늘은 {date_str}이야.

오늘 아내 정보:
- 이름: 이예원
- 생년월일: 1993년 01월 31일
- 직업: 첼로 선생님
- 현재 활동: 개인 레슨, NC백화점 레슨
- 과거 활동: 중학교, 초등학교 레슨
- 공연 활동: 순천시 주관 공연 참석 및 연주
- 가족 상황: 어제 6주 된 아이를 유산함

오늘의 날씨:
{weather_raw}

아래 항목을 정확히 지켜서 작성해줘. 이예원에게 보낼 수 있게, 따뜻하고 실제적인 문장으로 구성해줘.

🎻 이예원님의 오늘 메시지
━━━━━━━━━━━━━━━
🌤️ 오늘 날씨 한 줄 요약
• [순천 기준으로 간단히 정리]

💪 오늘 건강 관리
• [1993년 1월 31일생, 30대 후반 여성 기준 신체 관리법 — 식단/운동/수분 섭취 중심으로 3~4줄]

🧘 정신과 마음 챙김
• [최근 큰 상실을 겪은 상황에 맞춘 심리적 안정, 호흡/쉬기/지원 네트워크 팁 — 3~4줄]

📚 오늘 추천 책 또는 마음챙김 방법
• [부드럽게 힘이 되는 책 내용이나 자기 돌봄 방법 — 2~3가지]

🎼 첼로 선생님 일상 팁
• [현재 활동(개인 레슨/NC백화점)과 공연 준비를 위한 체력·마음 관리 팁 — 2~3줄]

💬 오늘 한마디
• [따뜻한 격려와 함께 오늘을 잘 견디자는 응원 한 문장]
━━━━━━━━━━━━━━━

주의사항: 감정에 공감하면서도 과도한 진단 없이 쓰고, 이모지 유지. 본문만 출력."""

    def claude_call(prompt, max_tokens=1200):
        import time
        for attempt in range(5):
            try:
                return client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                ).content[0].text
            except Exception as e:
                if "529" in str(e) or "overloaded" in str(e).lower():
                    wait = 15 * (attempt + 1)
                    print(f"  API 과부하, {wait}초 대기 후 재시도 ({attempt+1}/5)...")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError("Claude API 응답 실패 (5회 재시도 초과)")

    msg_baro = claude_call(prompt_baro)
    msg_spouse = claude_call(prompt_spouse)

    return msg_baro, msg_spouse
