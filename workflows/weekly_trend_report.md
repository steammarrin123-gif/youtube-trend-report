# 주간 브랜드 트렌드 리포트 Workflow

## 목표
매주 일요일 저녁 8시, 수익성 브랜드 / 콘텐츠 수익화 / 1인 사업 분야의
유튜브 트렌드를 자동 수집해서 PDF 리포트를 생성하고,
Gmail로 발송하고, Notion에 누적 저장한다.

## 실행 순서

### 1단계 — YouTube 수집 (`tools/youtube_collector.py`)
- 검색어 8개 (한국어 5개 + 영어 3개)로 최근 7일 인기 영상 수집
- 각 쿼리당 최대 10개, 중복 제거 후 조회수/좋아요 등 통계 수집
- 조회수 기준 내림차순 정렬

### 2단계 — 트렌드 분석 (`tools/trend_analyzer.py`)
- 10개 토픽 카테고리로 영상 분류
- 포맷별 분류 (쇼츠/숏폼/미드폼/롱폼)
- 채널별 성과 집계
- 콘텐츠 주제 추천 5개 자동 생성

### 3단계 — PDF 생성 (`tools/pdf_generator.py`)
- 저장 위치: `.tmp/trend_report_YYYYMMDD.pdf`
- 포함 내용: 요약 통계, 토픽 TOP 8, 포맷 분석, 채널 TOP 10, 주제 추천 TOP 5, 영상 목록 TOP 20

### 4단계 — Gmail 발송 (`tools/gmail_sender.py`)
- 수신자: steammarrin123@gmail.com (본인 이메일)
- PDF 첨부 발송

### 5단계 — Notion 저장 (`tools/notion_uploader.py`)
- 데이터베이스에 새 페이지 추가 (제목: YYYY-MM-DD 주간 트렌드 리포트)
- 전체 분석 데이터 블록 형태로 저장

## 자동 실행 설정
Windows 작업 스케줄러 — 매주 일요일 오후 8시
```
schtasks /create /tn "WeeklyTrendReport" /tr "cmd /c cd /d \"C:\Users\user\Desktop\클로드코드 유튜브 공부\" && python main.py >> logs\output.log 2>&1" /sc weekly /d SUN /st 20:00
```

## 문제 해결

| 오류 | 원인 | 해결 |
|------|------|------|
| `quotaExceeded` | YouTube API 일일 한도 초과 | 다음 날 자정 이후 재실행 |
| `SMTPAuthenticationError` | Gmail 앱 비밀번호 오류 | `.env`의 `GMAIL_APP_PASSWORD` 확인 (공백 없어야 함) |
| `APIResponseError` | Notion 통합 연결 안 됨 | Notion 페이지 → 연결 → 통합 다시 추가 |
| PDF 한글 깨짐 | 폰트 파일 없음 | `C:\Windows\Fonts\malgun.ttf` 존재 확인 |
| `ModuleNotFoundError` | 패키지 미설치 | `pip install -r requirements.txt` 재실행 |
