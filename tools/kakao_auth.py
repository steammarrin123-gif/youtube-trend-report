import os
import re
import json
import base64
import urllib.parse
import urllib.request
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
IN_GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"


def _write_env_value(key, value):
    if IN_GITHUB_ACTIONS:
        _update_github_secret(key, value)
        return
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(rf"^({re.escape(key)}=).*$", rf"\g<1>{value}", content, flags=re.MULTILINE)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def _update_github_secret(key, value):
    pat = os.environ.get("GH_PAT")
    repo = os.environ.get("GH_REPO")
    if not pat or not repo:
        return

    # 공개키 조회
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers={"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as res:
        pub_key_data = json.loads(res.read())

    # 값 암호화 (PyNaCl)
    from nacl import encoding, public as nacl_public
    public_key = nacl_public.PublicKey(pub_key_data["key"].encode(), encoding.Base64Encoder())
    sealed_box = nacl_public.SealedBox(public_key)
    encrypted = base64.b64encode(sealed_box.encrypt(value.encode())).decode()

    # 시크릿 업데이트
    body = json.dumps({"encrypted_value": encrypted, "key_id": pub_key_data["key_id"]}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/secrets/{key}",
        data=body,
        method="PUT",
        headers={
            "Authorization": f"Bearer {pat}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as res:
        pass


def refresh_access_token():
    load_dotenv(ENV_PATH, override=True)
    kakao_key = os.getenv("KAKAO_REST_API_KEY")
    refresh_token = os.getenv("KAKAO_REFRESH_TOKEN")

    if not refresh_token:
        raise ValueError("KAKAO_REFRESH_TOKEN이 없습니다. 카카오_인증_실행.bat을 먼저 실행해주세요.")

    client_secret = os.getenv("KAKAO_CLIENT_SECRET", "")
    params = {
        "grant_type": "refresh_token",
        "client_id": kakao_key,
        "refresh_token": refresh_token,
    }
    if client_secret:
        params["client_secret"] = client_secret
    data = urllib.parse.urlencode(params).encode()

    req = urllib.request.Request(
        "https://kauth.kakao.com/oauth/token",
        data=data,
        method="POST",
    )

    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read())

    new_access_token = result["access_token"]
    _write_env_value("KAKAO_ACCESS_TOKEN", new_access_token)
    os.environ["KAKAO_ACCESS_TOKEN"] = new_access_token

    if "refresh_token" in result:
        _write_env_value("KAKAO_REFRESH_TOKEN", result["refresh_token"])
        os.environ["KAKAO_REFRESH_TOKEN"] = result["refresh_token"]

    return new_access_token
