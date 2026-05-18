import os
import re
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_QUERIES = [
    ("수익성 브랜드", "ko"),
    ("콘텐츠 수익화", "ko"),
    ("1인 사업 런칭", "ko"),
    ("퍼스널 브랜드 만들기", "ko"),
    ("유튜브 수익화 방법", "ko"),
    ("profitable personal brand", "en"),
    ("content monetization strategy", "en"),
    ("solopreneur business launch", "en"),
]


def parse_duration_seconds(duration_str):
    hours = re.search(r'(\d+)H', duration_str)
    minutes = re.search(r'(\d+)M', duration_str)
    seconds = re.search(r'(\d+)S', duration_str)
    total = 0
    if hours:
        total += int(hours.group(1)) * 3600
    if minutes:
        total += int(minutes.group(1)) * 60
    if seconds:
        total += int(seconds.group(1))
    return total


def get_format_label(duration_seconds):
    if duration_seconds <= 180:
        return "쇼츠 (3분 이하)"
    elif duration_seconds <= 600:
        return "숏폼 (3~10분)"
    elif duration_seconds <= 1200:
        return "미드폼 (10~20분)"
    else:
        return "롱폼 (20분+)"


def collect_trending_videos(days_back=7, max_results_per_query=10):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=days_back)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    seen_ids = set()
    raw_videos = []

    for query, lang in SEARCH_QUERIES:
        try:
            response = youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                order="viewCount",
                publishedAfter=published_after,
                maxResults=max_results_per_query,
                relevanceLanguage=lang,
            ).execute()

            for item in response.get("items", []):
                vid_id = item["id"]["videoId"]
                if vid_id in seen_ids:
                    continue
                seen_ids.add(vid_id)
                raw_videos.append({
                    "video_id": vid_id,
                    "title": item["snippet"]["title"],
                    "channel_title": item["snippet"]["channelTitle"],
                    "channel_id": item["snippet"]["channelId"],
                    "published_at": item["snippet"]["publishedAt"],
                    "description": item["snippet"]["description"][:300],
                    "search_query": query,
                    "language": lang,
                })
        except Exception as e:
            print(f"  검색 오류 ({query}): {e}")

    if not raw_videos:
        return []

    video_ids = [v["video_id"] for v in raw_videos]
    stats_map = {}

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        try:
            stats_response = youtube.videos().list(
                part="statistics,contentDetails",
                id=",".join(chunk)
            ).execute()
            for item in stats_response.get("items", []):
                dur_secs = parse_duration_seconds(
                    item["contentDetails"].get("duration", "PT0S")
                )
                stats_map[item["id"]] = {
                    "view_count": int(item["statistics"].get("viewCount", 0)),
                    "like_count": int(item["statistics"].get("likeCount", 0)),
                    "comment_count": int(item["statistics"].get("commentCount", 0)),
                    "duration_seconds": dur_secs,
                    "format_label": get_format_label(dur_secs),
                }
        except Exception as e:
            print(f"  통계 수집 오류: {e}")

    videos = []
    for v in raw_videos:
        stats = stats_map.get(v["video_id"])
        if stats:
            v.update(stats)
            videos.append(v)

    videos.sort(key=lambda x: x.get("view_count", 0), reverse=True)
    return videos
