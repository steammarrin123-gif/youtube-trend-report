import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def send_report_email(pdf_path):
    gmail_address = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    today = datetime.now().strftime("%Y년 %m월 %d일")
    subject = f"[주간 트렌드 리포트] {today} — 수익성 브랜드·콘텐츠 수익화·1인 사업"

    body = f"""안녕하세요!

이번 주 ({today}) 주간 브랜드 트렌드 리포트가 준비됐습니다.

리포트 내용:
 - 수익성 브랜드 / 콘텐츠 수익화 / 1인 사업 분야 트렌딩 토픽 TOP 8
 - 포맷별 성과 분석 (쇼츠 vs 롱폼)
 - 이번 주 주목할 유튜브 채널 TOP 10
 - 이번 주 콘텐츠 주제 추천 TOP 5
 - 인기 영상 목록 TOP 20

첨부된 PDF를 확인해주세요.

---
자동 발송 시스템 | 매주 일요일 오후 8시 실행
"""

    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = gmail_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(pdf_path, "rb") as f:
        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=os.path.basename(pdf_path),
    )
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.send_message(msg)

    print(f"  이메일 발송 완료 → {gmail_address}")
    return True
