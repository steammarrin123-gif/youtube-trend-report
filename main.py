import sys
from datetime import datetime


def main():
    print(f"\n{'=' * 52}")
    print("  주간 브랜드 트렌드 리포트 시작")
    print(f"  실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 52}\n")

    # 1. YouTube 데이터 수집
    print("[1/5] YouTube 트렌딩 영상 수집 중...")
    from tools.youtube_collector import collect_trending_videos
    videos = collect_trending_videos(days_back=7)
    if not videos:
        print("  ERROR: 수집된 영상이 없습니다. YouTube API 키를 확인하세요.")
        sys.exit(1)
    print(f"  → {len(videos)}개 영상 수집 완료\n")

    # 2. 트렌드 분석
    print("[2/5] 트렌드 분석 중...")
    from tools.trend_analyzer import analyze_trends
    analysis = analyze_trends(videos)
    print(f"  → {len(analysis.get('top_topics', []))}개 토픽 분석 완료\n")

    # 3. PDF 생성
    print("[3/5] PDF 리포트 생성 중...")
    from tools.pdf_generator import generate_report
    pdf_path = generate_report(analysis)
    print()

    # 4. Gmail 발송
    print("[4/5] 이메일 발송 중...")
    from tools.gmail_sender import send_report_email
    send_report_email(pdf_path)
    print()

    # 5. Notion 저장
    print("[5/5] Notion 저장 중...")
    from tools.notion_uploader import upload_weekly_report
    page_url = upload_weekly_report(analysis)
    print()

    print(f"{'=' * 52}")
    print("  완료!")
    print(f"  PDF  : {pdf_path}")
    print(f"  Notion: {page_url}")
    print(f"{'=' * 52}\n")


if __name__ == "__main__":
    main()
