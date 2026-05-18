from collections import defaultdict
from datetime import datetime

TOPIC_CATEGORIES = {
    "AI 활용": ["ai", "chatgpt", "gpt", "인공지능", "claude", "자동화", "automation"],
    "유튜브 성장": ["유튜브", "youtube", "구독자", "알고리즘", "썸네일", "shorts", "쇼츠"],
    "수익화 전략": ["수익화", "monetize", "수익", "revenue", "income", "passive", "돈 버는"],
    "퍼스널 브랜드": ["퍼스널 브랜드", "personal brand", "브랜딩", "branding", "정체성"],
    "1인 사업": ["1인", "solopreneur", "freelance", "프리랜서", "solo", "창업"],
    "콘텐츠 전략": ["콘텐츠 전략", "content strategy", "아이디어", "기획", "스크립트"],
    "이메일 마케팅": ["이메일", "email", "newsletter", "뉴스레터"],
    "SNS 마케팅": ["인스타그램", "instagram", "틱톡", "tiktok", "sns", "소셜미디어"],
    "디지털 제품": ["디지털 제품", "digital product", "코스", "course", "강의", "ebook"],
    "마인드셋": ["마인드셋", "mindset", "성공 습관", "루틴", "routine"],
}


def detect_topics(text):
    text_lower = text.lower()
    found = [t for t, kws in TOPIC_CATEGORIES.items() if any(k in text_lower for k in kws)]
    return found if found else ["기타"]


def format_views(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def analyze_trends(videos):
    if not videos:
        return {}

    topic_stats = defaultdict(lambda: {"count": 0, "total_views": 0, "total_likes": 0, "videos": []})
    for v in videos:
        combined = f"{v.get('title', '')} {v.get('description', '')}"
        for topic in detect_topics(combined):
            topic_stats[topic]["count"] += 1
            topic_stats[topic]["total_views"] += v.get("view_count", 0)
            topic_stats[topic]["total_likes"] += v.get("like_count", 0)
            topic_stats[topic]["videos"].append(v.get("title", ""))

    format_stats = defaultdict(lambda: {"count": 0, "total_views": 0})
    for v in videos:
        fmt = v.get("format_label", "알 수 없음")
        format_stats[fmt]["count"] += 1
        format_stats[fmt]["total_views"] += v.get("view_count", 0)

    channel_stats = defaultdict(lambda: {"count": 0, "total_views": 0})
    for v in videos:
        ch = v.get("channel_title", "알 수 없음")
        channel_stats[ch]["count"] += 1
        channel_stats[ch]["total_views"] += v.get("view_count", 0)

    sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1]["total_views"], reverse=True)
    sorted_formats = sorted(format_stats.items(), key=lambda x: x[1]["total_views"], reverse=True)
    sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]["total_views"], reverse=True)[:10]

    recommendations = _generate_recommendations(sorted_topics, sorted_formats)

    return {
        "collection_date": datetime.now().strftime("%Y-%m-%d"),
        "total_videos": len(videos),
        "total_views": sum(v.get("view_count", 0) for v in videos),
        "top_topics": sorted_topics[:8],
        "format_distribution": sorted_formats,
        "top_channels": sorted_channels,
        "recommendations": recommendations,
        "top_videos": videos[:20],
    }


def _generate_recommendations(sorted_topics, sorted_formats):
    top_format = sorted_formats[0][0] if sorted_formats else "미드폼 (10~20분)"
    format_hints = {
        "AI": "튜토리얼 + 롱폼",
        "유튜브": "쇼츠 시리즈",
        "수익화": "케이스스터디 형식",
        "브랜드": "개인 스토리 + 롱폼",
        "사업": "케이스스터디 형식",
        "SNS": "쇼츠 시리즈",
        "디지털": "튜토리얼 형식",
    }

    recommendations = []
    for i, (topic, stats) in enumerate(sorted_topics[:5]):
        avg_views = stats["total_views"] // stats["count"] if stats["count"] > 0 else 0
        hint = next((v for k, v in format_hints.items() if k in topic), top_format)
        recommendations.append({
            "rank": i + 1,
            "topic": topic,
            "reason": f"이번 주 평균 조회수 {format_views(avg_views)}회 ({stats['count']}개 영상)",
            "format": hint,
            "sample_titles": stats["videos"][:2],
        })

    return recommendations
