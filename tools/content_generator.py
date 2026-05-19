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

    weather_block = (
        f"🌤️ 순천\n{weather_suncheon}\n\n"
        f"{gwangyang_section}\n\n"
        f"{yeosu_section}"
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # 날씨 데이터 수집 (순천, 광양, 여수)
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

    weather_prompt = f"""오늘은 {date_str}이야.

날씨 데이터:
{weather_raw}

아이 둘(정바로 {ages['baro_months']}개월, 왕눈이 임신 {ages['preg_weeks']}주)은 순천에만 있어.
와이프는 임신 중이야.

아래 형식으로 짧고 실용적인 날씨 메시지 써줘:

🌤️ {date_str} 날씨
━━━━━━━━━━━━━━━
🏙️ 순천 | {sc['temp'] if sc else '?'}°C ({sc['min'] if sc else '?'}~{sc['max'] if sc else '?'}°C) | {sc['rain'] if sc else '?'}
🏭 광양 | {gw['temp'] if gw else '?'}°C ({gw['min'] if gw else '?'}~{gw['max'] if gw else '?'}°C) | {gw['rain'] if gw else '?'}
🌊 여수 | {ys['temp'] if ys else '?'}°C ({ys['min'] if ys else '?'}~{ys['max'] if ys else '?'}°C) | {ys['rain'] if ys else '?'}

👶 정바로 오늘 날씨 대응
• [순천 날씨 기준으로 {ages['baro_months']}개월 아이 옷차림, 외출 시 주의사항 — 2줄]

🤰 와이프 오늘 준비사항
• [임신 {ages['preg_weeks']}주 임산부 기준 날씨 대응, 준비물 — 2줄]
━━━━━━━━━━━━━━━

주의사항: 이모지 유지. 본문만 출력."""

    msg_weather = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": weather_prompt}],
    ).content[0].text

    # 2번 메시지: 정바로
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

    # 3번 메시지: 왕눈이
    prompt_wangnuni = f"""오늘은 {date_str}이야.
둘째: 왕눈이 (임신 {ages['preg_weeks']}주 {ages['preg_day']}일, 출산예정일 2027년 1월 10일, D-{ages['days_left']}일)

아래 형식을 정확히 따라줘. 각 항목 3~4줄로 자세하게 써줘:

🤰 왕눈이 ({ages['preg_weeks']}주 {ages['preg_day']}일, D-{ages['days_left']})
━━━━━━━━━━━━━━━
👶 이번 주 태아 발달
• [현재 주차 태아의 크기/발달 상황 — 3~4줄, 구체적으로]

💊 엄마 몸 변화
• [이 주차 흔한 증상과 대처법 — 3줄]

🥗 이번 주 추천 음식
• [좋은 음식 2~3가지와 이유]

👨 아빠가 오늘 할 일
• [실천할 수 있는 행동 2~3가지]

💬 오늘의 태담
• [왕눈이에게 보내는 따뜻한 태담 한 문장]
━━━━━━━━━━━━━━━

주의사항: 의학적으로 정확한 정보만. 이모지 유지. 본문만 출력."""

    msg_baro = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt_baro}],
    ).content[0].text

    msg_wangnuni = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt_wangnuni}],
    ).content[0].text

    # 4번 메시지: 배 둘러보기
    gw_info = _get_marine_info("Gwangyang")
    ys_info = _get_marine_info("Yeosu")
    gw_tide = _get_tide_info("광양")
    ys_tide = _get_tide_info("여수")

    marine_raw = ""
    if gw_info:
        marine_raw += f"광양: 비={gw_info['rain']}, 바람={gw_info['wind_ms']}m/s, 파도={gw_info['wave']}"
        if gw_tide:
            marine_raw += f", 고조={gw_tide['고조']}, 저조={gw_tide['저조']}"
        marine_raw += "\n"
    if ys_info:
        marine_raw += f"여수: 비={ys_info['rain']}, 바람={ys_info['wind_ms']}m/s, 파도={ys_info['wave']}"
        if ys_tide:
            marine_raw += f", 고조={ys_tide['고조']}, 저조={ys_tide['저조']}"

    prompt_boat = f"""오늘은 {date_str}이야.

오늘 해양 날씨:
{marine_raw if marine_raw else '해양 정보 없음'}

배를 가지고 있고 오늘 아침 배를 둘러봐야 해.

아래 형식으로 실용적인 '배 둘러보기' 체크리스트 메시지를 써줘:

⛵ {date_str} 배 둘러보기
━━━━━━━━━━━━━━━
🌊 오늘 해상 상황
• [오늘 날씨/바람/파도 기준으로 출항 가능 여부 또는 주의사항 — 2줄]

🔍 오늘 점검 항목
• [오늘 날씨/상황에 맞는 배 점검 항목 4~5가지 — 각 한 줄씩]

⚠️ 오늘 특별 주의사항
• [날씨나 계절에 맞는 주의사항 1~2가지]

💡 오늘의 한마디
• [배 관리나 안전에 대한 짧은 팁 한 줄]
━━━━━━━━━━━━━━━

주의사항: 이모지 유지. 본문만 출력."""

    msg_boat = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt_boat}],
    ).content[0].text

    return msg_weather, msg_baro, msg_wangnuni, msg_boat
