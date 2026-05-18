"""
카카오톡 최초 인증 스크립트 — 처음 한 번만 실행하면 됩니다.
"""
import os
import re
import sys
import json
import urllib.parse
import urllib.request
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
REDIRECT_URI = "http://localhost:5000/callback"

with open(ENV_PATH, "r", encoding="utf-8") as f:
    _env_text = f.read()

KAKAO_KEY = re.search(r"KAKAO_REST_API_KEY=(.+)", _env_text).group(1).strip()

auth_code = None
done_event = threading.Event()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in qs:
            auth_code = qs["code"][0]
            msg = b"<h2>&#51064;&#51613; &#50756;&#47308;! &#51060; &#52285;&#51012; &#45803;&#44256; &#53552;&#48120;&#45903;&#47196; &#46028;&#50500;&#44032;&#49464;&#50836;.</h2>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
        else:
            self.send_response(400)
            self.end_headers()
        done_event.set()

    def log_message(self, *args):
        pass


def save_tokens(access_token, refresh_token):
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r"^(KAKAO_ACCESS_TOKEN=).*$", f"\\g<1>{access_token}", content, flags=re.MULTILINE)
    content = re.sub(r"^(KAKAO_REFRESH_TOKEN=).*$", f"\\g<1>{refresh_token}", content, flags=re.MULTILINE)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"저장 완료: {ENV_PATH}")


def get_tokens_from_code(code):
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": KAKAO_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }).encode()
    req = urllib.request.Request("https://kauth.kakao.com/oauth/token", data=data, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


def main():
    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_KEY}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&response_type=code"
    )

    print("\n" + "=" * 55)
    print("  카카오톡 인증을 시작합니다.")
    print("=" * 55)
    print(f"\n.env 경로: {ENV_PATH}")
    print(f"카카오 앱키: {KAKAO_KEY[:8]}...\n")

    # 로컬 서버 먼저 실행
    server = HTTPServer(("localhost", 5000), Handler)
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()

    print("브라우저를 열고 로그인해주세요...")
    webbrowser.open(auth_url)

    print("로그인 대기 중 (최대 3분)...\n")
    done_event.wait(timeout=180)
    t.join(timeout=5)

    if not auth_code:
        print("\n[실패] 자동 인증 실패. 수동으로 진행합니다.")
        print(f"\n아래 URL을 브라우저에 직접 복사해서 열어주세요:")
        print(f"\n{auth_url}\n")
        print("로그인 후 브라우저 주소창에 보이는 URL 전체를 복사해서 붙여넣어 주세요.")
        print("(http://localhost:5000/callback?code=... 형태의 URL)")
        redirected_url = input("\n리다이렉트된 URL 붙여넣기: ").strip()
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(redirected_url).query)
        if "code" not in qs:
            print("URL에서 code를 찾을 수 없습니다.")
            input("엔터를 눌러 종료...")
            return
        code = qs["code"][0]
    else:
        code = auth_code

    print(f"\n인증 코드 수신: {code[:15]}...")
    print("토큰 발급 중...")

    try:
        tokens = get_tokens_from_code(code)
    except Exception as e:
        print(f"\n[오류] 토큰 발급 실패: {e}")
        input("엔터를 눌러 종료...")
        return

    save_tokens(tokens["access_token"], tokens["refresh_token"])

    print("\n" + "=" * 55)
    print("  카카오톡 인증 완료!")
    print(f"  액세스 토큰: {tokens['access_token'][:20]}...")
    print(f"  리프레시 토큰: {tokens['refresh_token'][:20]}...")
    print("=" * 55)
    print("\n이제 main_parenting.py 를 실행하면 카카오톡이 발송됩니다.\n")
    input("엔터를 눌러 종료...")


if __name__ == "__main__":
    main()
