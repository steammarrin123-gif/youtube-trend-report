import os
from datetime import datetime
from fpdf import FPDF

FONT_REGULAR = r"C:\Windows\Fonts\malgun.ttf"
FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"

BLUE = (41, 98, 255)
DARK = (30, 30, 30)
GRAY = (120, 120, 120)
LIGHT_GRAY = (245, 245, 245)
WHITE = (255, 255, 255)


def _fmt(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("Malgun", style="", fname=FONT_REGULAR)
        self.add_font("Malgun", style="B", fname=FONT_BOLD)
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(20, 20, 20)

    def footer(self):
        self.set_y(-12)
        self.set_font("Malgun", size=8)
        self.set_text_color(*GRAY)
        self.cell(
            0, 8,
            f"주간 브랜드 트렌드 리포트  |  {datetime.now().strftime('%Y년 %m월 %d일')}  |  {self.page_no()} 페이지",
            align="C",
        )
        self.set_text_color(*DARK)

    def section_title(self, title):
        self.ln(5)
        self.set_fill_color(*BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Malgun", style="B", size=11)
        self.cell(0, 9, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(*DARK)

    def _stat_box(self, label, value, x, y, w=38, h=22):
        self.set_xy(x, y)
        self.set_fill_color(230, 238, 255)
        self.rect(x, y, w, h, style="F")
        self.set_xy(x, y + 2)
        self.set_font("Malgun", style="B", size=13)
        self.set_text_color(*BLUE)
        self.cell(w, 9, value, align="C")
        self.set_xy(x, y + 13)
        self.set_font("Malgun", size=7)
        self.set_text_color(*GRAY)
        self.cell(w, 6, label, align="C")
        self.set_text_color(*DARK)


def generate_report(analysis, output_dir=".tmp"):
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = os.path.join(output_dir, f"trend_report_{date_str}.pdf")

    pdf = ReportPDF()

    # ── 표지 ──────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, 210, 70, style="F")

    pdf.set_y(18)
    pdf.set_font("Malgun", style="B", size=20)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 12, "주간 브랜드 트렌드 리포트", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Malgun", size=11)
    pdf.set_text_color(200, 218, 255)
    pdf.cell(0, 8, "수익성 브랜드 · 콘텐츠 수익화 · 1인 사업 런칭", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Malgun", size=10)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 7, analysis.get("collection_date", ""), align="C", new_x="LMARGIN", new_y="NEXT")

    # 요약 통계 박스 4개
    top_topics = analysis.get("top_topics", [])
    pdf._stat_box("분석 영상 수", f"{analysis.get('total_videos', 0)}개", 20, 82)
    pdf._stat_box("총 조회수", _fmt(analysis.get("total_views", 0)), 64, 82)
    pdf._stat_box("발굴 토픽", f"{len(top_topics)}개", 108, 82)
    pdf._stat_box("분석 기간", "최근 7일", 152, 82)

    # ── 트렌딩 토픽 ───────────────────────────────────
    pdf.set_y(118)
    pdf.section_title("이번 주 트렌딩 토픽 TOP 8")
    pdf.set_font("Malgun", size=10)

    for i, (topic, stats) in enumerate(top_topics[:8]):
        avg_v = stats["total_views"] // stats["count"] if stats["count"] > 0 else 0
        badge_color = BLUE if i < 3 else GRAY
        pdf.set_fill_color(*badge_color)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Malgun", style="B", size=9)
        pdf.cell(7, 7, str(i + 1), fill=True, align="C")

        pdf.set_text_color(*DARK)
        pdf.set_font("Malgun", style="B", size=10)
        pdf.cell(52, 7, topic)

        pdf.set_font("Malgun", size=9)
        pdf.set_text_color(*GRAY)
        pdf.cell(38, 7, f"영상 {stats['count']}개")
        pdf.cell(0, 7, f"평균 조회수 {_fmt(avg_v)}회", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*DARK)

    # ── 포맷 분석 ─────────────────────────────────────
    if pdf.get_y() > 230:
        pdf.add_page()
    pdf.section_title("포맷별 성과 분석")
    pdf.set_font("Malgun", size=10)

    for fmt_label, stats in analysis.get("format_distribution", []):
        avg_v = stats["total_views"] // stats["count"] if stats["count"] > 0 else 0
        pdf.set_text_color(*DARK)
        pdf.cell(58, 7, fmt_label)
        pdf.set_text_color(*GRAY)
        pdf.cell(35, 7, f"영상 {stats['count']}개")
        pdf.cell(0, 7, f"평균 조회수 {_fmt(avg_v)}회", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*DARK)

    # ── 주목 채널 TOP 10 ──────────────────────────────
    if pdf.get_y() > 220:
        pdf.add_page()
    pdf.section_title("이번 주 주목할 채널 TOP 10")
    pdf.set_font("Malgun", size=10)

    for i, (channel, stats) in enumerate(analysis.get("top_channels", [])[:10]):
        pdf.set_text_color(*GRAY)
        pdf.set_font("Malgun", size=9)
        pdf.cell(8, 7, f"{i + 1}.")
        pdf.set_font("Malgun", style="B", size=10)
        pdf.set_text_color(*DARK)
        ch_name = channel[:32] + ("…" if len(channel) > 32 else "")
        pdf.cell(78, 7, ch_name)
        pdf.set_font("Malgun", size=9)
        pdf.set_text_color(*GRAY)
        pdf.cell(35, 7, f"영상 {stats['count']}개")
        pdf.cell(0, 7, f"총 {_fmt(stats['total_views'])}회", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*DARK)

    # ── 콘텐츠 주제 추천 TOP 5 ────────────────────────
    pdf.add_page()
    pdf.section_title("이번 주 콘텐츠 주제 추천 TOP 5")

    for rec in analysis.get("recommendations", [])[:5]:
        pdf.set_font("Malgun", style="B", size=11)
        pdf.set_text_color(*BLUE)
        pdf.cell(0, 8, f"추천 {rec['rank']}. {rec['topic']}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Malgun", size=10)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 7, f"  추천 이유: {rec['reason']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"  추천 포맷: {rec['format']}", new_x="LMARGIN", new_y="NEXT")

        if rec.get("sample_titles"):
            pdf.set_font("Malgun", size=9)
            pdf.set_text_color(*GRAY)
            for t in rec["sample_titles"][:2]:
                short = t[:65] + "…" if len(t) > 65 else t
                pdf.cell(0, 6, f"  참고 영상: {short}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(4)
        pdf.set_text_color(*DARK)

    # ── 인기 영상 목록 TOP 20 ─────────────────────────
    if pdf.get_y() > 220:
        pdf.add_page()
    pdf.section_title("이번 주 인기 영상 TOP 20")

    # 헤더
    pdf.set_fill_color(*BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Malgun", style="B", size=8)
    pdf.cell(7, 7, "#", fill=True, align="C")
    pdf.cell(88, 7, "제목", fill=True)
    pdf.cell(43, 7, "채널", fill=True)
    pdf.cell(22, 7, "조회수", fill=True, align="R")
    pdf.cell(0, 7, "포맷", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*DARK)

    pdf.set_font("Malgun", size=8)
    for i, v in enumerate(analysis.get("top_videos", [])[:20]):
        if pdf.get_y() > 268:
            pdf.add_page()

        fill = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if fill else WHITE))

        title = v.get("title", "")
        title = (title[:44] + "…") if len(title) > 44 else title
        channel = v.get("channel_title", "")
        channel = (channel[:20] + "…") if len(channel) > 20 else channel

        pdf.cell(7, 6, str(i + 1), fill=fill, align="C")
        pdf.cell(88, 6, title, fill=fill)
        pdf.cell(43, 6, channel, fill=fill)
        pdf.cell(22, 6, _fmt(v.get("view_count", 0)), fill=fill, align="R")
        fmt = v.get("format_label", "")[:10]
        pdf.cell(0, 6, fmt, fill=fill, new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)
    print(f"  PDF 생성 완료: {output_path}")
    return output_path
