import os
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()


def _fmt(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _paragraph(text):
    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)]
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]},
        }
        for c in chunks
    ]


def _heading(text, level=2):
    t = f"heading_{level}"
    return {"object": "block", "type": t, t: {"rich_text": [{"type": "text", "text": {"content": text}}]}}


def _bullet(text):
    text = text[:1900]
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _divider():
    return {"object": "block", "type": "divider", "divider": {}}


def _get_title_property(notion, ds_id):
    result = notion.search(filter={"value": "data_source", "property": "object"})
    for item in result.get("results", []):
        if item["id"].replace("-", "") == ds_id.replace("-", ""):
            for name, prop in item.get("properties", {}).items():
                if prop["type"] == "title":
                    return name
    return "Name"


def upload_weekly_report(analysis):
    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    db_id = os.getenv("NOTION_DATABASE_ID")

    title_prop = _get_title_property(notion, db_id)
    today = datetime.now().strftime("%Y-%m-%d")
    page_title = f"{today} 주간 트렌드 리포트"

    blocks = []

    # 요약
    blocks.append(_heading("📊 이번 주 요약", 2))
    blocks.append(_bullet(f"분석 영상 수: {analysis.get('total_videos', 0)}개"))
    blocks.append(_bullet(f"총 조회수: {_fmt(analysis.get('total_views', 0))}회"))
    blocks.append(_bullet(f"분석 기간: 최근 7일 ({today} 기준)"))
    blocks.append(_divider())

    # 트렌딩 토픽
    blocks.append(_heading("🔥 트렌딩 토픽 TOP 8", 2))
    for i, (topic, stats) in enumerate(analysis.get("top_topics", [])[:8]):
        avg_v = stats["total_views"] // stats["count"] if stats["count"] > 0 else 0
        blocks.append(_bullet(f"{i + 1}. {topic} — 영상 {stats['count']}개, 평균 조회수 {_fmt(avg_v)}회"))
    blocks.append(_divider())

    # 포맷 분석
    blocks.append(_heading("📹 포맷별 성과", 2))
    for fmt_label, stats in analysis.get("format_distribution", []):
        avg_v = stats["total_views"] // stats["count"] if stats["count"] > 0 else 0
        blocks.append(_bullet(f"{fmt_label} — {stats['count']}개, 평균 {_fmt(avg_v)}회"))
    blocks.append(_divider())

    # 채널 TOP 10
    blocks.append(_heading("📺 주목 채널 TOP 10", 2))
    for i, (channel, stats) in enumerate(analysis.get("top_channels", [])[:10]):
        blocks.append(_bullet(f"{i + 1}. {channel} — {stats['count']}개 영상, {_fmt(stats['total_views'])}회"))
    blocks.append(_divider())

    # 콘텐츠 추천
    blocks.append(_heading("💡 콘텐츠 주제 추천 TOP 5", 2))
    for rec in analysis.get("recommendations", []):
        blocks.append(_bullet(
            f"추천 {rec['rank']}. [{rec['topic']}] {rec['reason']} | 추천 포맷: {rec['format']}"
        ))
    blocks.append(_divider())

    # 인기 영상 목록
    blocks.append(_heading("🎬 인기 영상 TOP 20", 2))
    for i, v in enumerate(analysis.get("top_videos", [])[:20]):
        blocks.append(_bullet(
            f"{i + 1}. {v.get('title', '')} | {v.get('channel_title', '')} | {_fmt(v.get('view_count', 0))}회 | {v.get('format_label', '')}"
        ))

    # Notion API: 한 번에 최대 100 블록
    page = notion.pages.create(
        parent={"data_source_id": db_id},
        properties={
            title_prop: {
                "title": [{"type": "text", "text": {"content": page_title}}]
            }
        },
        children=blocks[:100],
    )
    page_id = page["id"]

    # 100개 초과분 추가
    for i in range(100, len(blocks), 100):
        notion.blocks.children.append(page_id, children=blocks[i:i + 100])

    page_url = page.get("url", "")
    print(f"  Notion 저장 완료: {page_url}")
    return page_url
