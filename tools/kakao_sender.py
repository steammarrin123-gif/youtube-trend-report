import os
import json
import urllib.parse
import urllib.request
from dotenv import load_dotenv
from tools.kakao_auth import refresh_access_token

load_dotenv()


def send_to_me(message_text):
    # 매번 토큰 갱신 (6시간 만료 대비)
    access_token = refresh_access_token()

    template = json.dumps({
        "object_type": "text",
        "text": message_text,
        "link": {"web_url": "", "mobile_web_url": ""},
    }, ensure_ascii=False)

    data = urllib.parse.urlencode({"template_object": template}).encode("utf-8")

    req = urllib.request.Request(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        data=data,
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")

    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read())

    if result.get("result_code") == 0:
        print("  카카오톡 발송 완료")
    else:
        raise RuntimeError(f"카카오톡 발송 실패: {result}")

    return result
