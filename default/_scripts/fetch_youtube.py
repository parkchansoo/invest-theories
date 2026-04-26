#!/usr/bin/env python3
"""
유튜브 영상 스크립트(자막) + 메타데이터 수집
사용법:
  python fetch_youtube.py <youtube_url> [--api-key YOUR_KEY] [--lang ko] [--output-dir <path>]

예시:
  python fetch_youtube.py "https://www.youtube.com/watch?v=xxxxx"
  python fetch_youtube.py "https://youtu.be/xxxxx" --lang en
  python fetch_youtube.py "https://www.youtube.com/watch?v=xxxxx" --api-key AIza... --lang ko

기능:
  1) yt-dlp로 자막(수동/자동) 추출
  2) YouTube Data API v3으로 상세 메타데이터 조회 (API 키 있을 때)
  3) 옵시디언 노트로 저장
"""

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("yt-dlp가 설치되지 않았습니다. pip install yt-dlp")
    sys.exit(1)


# ─── 설정 ───────────────────────────────────────────────
# .env 파일에서 키 로드
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().strip().split("\n"):
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# YouTube Data API 키 — 없어도 yt-dlp만으로 자막 추출 가능
DEFAULT_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
# ─────────────────────────────────────────────────────────


def extract_video_id(url: str) -> str:
    """URL에서 비디오 ID를 추출합니다."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return url


def fetch_with_ytdlp(url: str, lang: str = "ko") -> dict:
    """yt-dlp로 영상 정보와 자막을 추출합니다."""
    result = {"subtitles_text": "", "info": {}}

    # 1단계: 영상 정보 추출
    info_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    result["info"] = {
        "title": info.get("title", ""),
        "channel": info.get("channel", "") or info.get("uploader", ""),
        "channel_url": info.get("channel_url", "") or info.get("uploader_url", ""),
        "upload_date": info.get("upload_date", ""),
        "duration": info.get("duration", 0),
        "view_count": info.get("view_count", 0),
        "like_count": info.get("like_count", 0),
        "description": info.get("description", ""),
        "tags": info.get("tags", []),
        "thumbnail": info.get("thumbnail", ""),
        "video_id": info.get("id", ""),
        "webpage_url": info.get("webpage_url", url),
    }

    # 2단계: 자막 추출
    # 시도 순서: 수동자막(lang) → 자동자막(lang) → 수동자막(en) → 자동자막(en)
    subs = info.get("subtitles", {})
    auto_subs = info.get("automatic_captions", {})

    sub_lang = None
    is_auto = False

    # 수동 자막 확인
    if lang in subs:
        sub_lang = lang
    elif "en" in subs and lang != "en":
        sub_lang = "en"

    # 자동 자막 확인 (수동 없을 때)
    if not sub_lang:
        is_auto = True
        if lang in auto_subs:
            sub_lang = lang
        elif f"{lang}-orig" in auto_subs:
            sub_lang = f"{lang}-orig"
        elif "ko" in auto_subs:
            sub_lang = "ko"
        elif "en" in auto_subs:
            sub_lang = "en"
        # 번역 자막 시도 (예: ko-en)
        elif f"ko-en" in auto_subs:
            sub_lang = "ko-en"

    if sub_lang:
        result["subtitle_lang"] = sub_lang
        result["subtitle_auto"] = is_auto

        # 자막 다운로드
        with tempfile.TemporaryDirectory() as tmpdir:
            sub_opts = {
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
                "outtmpl": os.path.join(tmpdir, "sub"),
                "writesubtitles": not is_auto,
                "writeautomaticsub": is_auto,
                "subtitleslangs": [sub_lang],
                "subtitlesformat": "srt/vtt/best",
                "postprocessors": [],
            }
            with yt_dlp.YoutubeDL(sub_opts) as ydl:
                ydl.download([url])

            # 자막 파일 찾기
            sub_text = ""
            for f in Path(tmpdir).glob("*"):
                if f.suffix in [".srt", ".vtt", ".ttml"]:
                    raw = f.read_text(encoding="utf-8", errors="replace")
                    sub_text = clean_subtitle_text(raw, f.suffix)
                    break

            result["subtitles_text"] = sub_text
    else:
        result["subtitle_lang"] = None
        result["subtitle_auto"] = None
        result["subtitles_text"] = "(자막을 찾을 수 없습니다)"

    return result


def clean_subtitle_text(raw: str, ext: str) -> str:
    """자막 파일에서 타임코드/태그를 제거하고 텍스트만 추출합니다."""
    lines = raw.split("\n")
    text_lines = []

    if ext == ".srt":
        for line in lines:
            line = line.strip()
            # 숫자만 있는 줄 (인덱스) 건너뛰기
            if re.match(r"^\d+$", line):
                continue
            # 타임코드 줄 건너뛰기
            if re.match(r"\d{2}:\d{2}:\d{2}", line):
                continue
            if line:
                # HTML 태그 제거
                clean = re.sub(r"<[^>]+>", "", line)
                if clean and clean not in text_lines[-1:]:
                    text_lines.append(clean)
    elif ext == ".vtt":
        in_header = True
        for line in lines:
            line = line.strip()
            if in_header:
                if line == "":
                    in_header = False
                continue
            if re.match(r"\d{2}:\d{2}:\d{2}\.", line):
                continue
            if re.match(r"^\d+$", line):
                continue
            if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            if line:
                clean = re.sub(r"<[^>]+>", "", line)
                if clean and clean not in text_lines[-1:]:
                    text_lines.append(clean)
    else:
        # 기타: 태그만 제거
        for line in lines:
            clean = re.sub(r"<[^>]+>", "", line).strip()
            if clean:
                text_lines.append(clean)

    return "\n".join(text_lines)


def fetch_with_youtube_api(video_id: str, api_key: str) -> dict:
    """YouTube Data API v3으로 상세 메타데이터를 조회합니다."""
    try:
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", developerKey=api_key)

        # 영상 상세 정보
        response = youtube.videos().list(
            part="snippet,statistics,contentDetails,topicDetails",
            id=video_id
        ).execute()

        if not response.get("items"):
            return {}

        item = response["items"][0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})
        topics = item.get("topicDetails", {})

        return {
            "api_title": snippet.get("title"),
            "api_description": snippet.get("description"),
            "api_channel": snippet.get("channelTitle"),
            "api_channel_id": snippet.get("channelId"),
            "api_published_at": snippet.get("publishedAt"),
            "api_tags": snippet.get("tags", []),
            "api_category_id": snippet.get("categoryId"),
            "api_default_language": snippet.get("defaultLanguage"),
            "api_default_audio_language": snippet.get("defaultAudioLanguage"),
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "duration_iso": content.get("duration"),
            "definition": content.get("definition"),
            "caption": content.get("caption"),
            "topic_categories": topics.get("topicCategories", []),
        }
    except Exception as e:
        print(f"  ⚠️ YouTube API 조회 실패: {e}")
        return {}


def format_duration(seconds: int) -> str:
    """초를 HH:MM:SS 형태로 변환합니다."""
    if not seconds:
        return "N/A"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_number(n: int) -> str:
    """숫자를 읽기 쉬운 형태로 포맷합니다."""
    if not n:
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


def generate_markdown(data: dict, api_data: dict, url: str) -> str:
    """옵시디언 노트를 생성합니다."""
    info = data["info"]
    today = datetime.now().strftime("%Y-%m-%d")
    upload_date = info.get("upload_date", "")
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

    tags_list = info.get("tags", []) or api_data.get("api_tags", [])
    tags_str = ", ".join(tags_list[:10]) if tags_list else ""

    sub_info = ""
    if data.get("subtitle_lang"):
        sub_type = "자동 생성" if data.get("subtitle_auto") else "수동"
        sub_info = f"{data['subtitle_lang']} ({sub_type})"
    else:
        sub_info = "없음"

    # 설명문 (API가 더 완전할 수 있음)
    description = api_data.get("api_description") or info.get("description", "")

    md = f"""---
title: "{info['title']}"
channel: "{info['channel']}"
url: "{info['webpage_url']}"
upload_date: "{upload_date}"
collected: "{today}"
tags:
  - 유튜브
  - 클리핑
---

# {info['title']}

## 영상 정보

| 항목 | 내용 |
|------|------|
| **채널** | [{info['channel']}]({info.get('channel_url', '')}) |
| **업로드** | {upload_date} |
| **길이** | {format_duration(info.get('duration', 0))} |
| **조회수** | {format_number(api_data.get('view_count') or info.get('view_count', 0))} |
| **좋아요** | {format_number(api_data.get('like_count') or info.get('like_count', 0))} |
| **댓글** | {format_number(api_data.get('comment_count', 0))} |
| **자막** | {sub_info} |
| **URL** | [YouTube 링크]({info['webpage_url']}) |

"""

    if tags_str:
        md += f"**태그**: {tags_str}\n\n"

    # 썸네일
    if info.get("thumbnail"):
        md += f"![thumbnail]({info['thumbnail']})\n\n"

    # 영상 설명 (전문 보존)
    if description:
        md += f"""## 영상 설명

{description}

"""

    # 자막/스크립트 (전문 보존 — 원문을 최대한 살림)
    sub_text = data.get('subtitles_text', '')
    if sub_text:
        md += f"""## 전체 스크립트 (자막 원문)

> 아래는 영상의 자막을 그대로 추출한 전문입니다.
> 단락 구분이 없을 수 있으니, 필요 시 Claude에게 단락 정리를 요청하세요.

{sub_text}

"""
    else:
        md += """## 전체 스크립트 (자막 원문)

(자막을 가져올 수 없습니다)

"""

    md += """---

## 요약 (5줄)
> (Claude에게 요약 요청 — 예: "이 영상 내용 5줄로 요약해줘")

1.
2.
3.
4.
5.

## 투자 관련 인사이트
>

## 관련 종목
-

## 내 생각
>

## 후속 조치
- [ ] 관련 종목 분석 노트에 링크
- [ ] 추가 리서치 필요 여부 확인
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="유튜브 영상 스크립트/메타데이터 수집")
    parser.add_argument("url", help="유튜브 URL 또는 비디오 ID")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="YouTube Data API v3 키")
    parser.add_argument("--lang", default="ko", help="선호 자막 언어 (기본: ko)")
    parser.add_argument("--output-dir", default=None, help="출력 디렉토리")
    parser.add_argument("--json", action="store_true", help="JSON으로도 저장")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)

    print(f"🎬 유튜브 영상 수집 중: {video_id}")

    try:
        # 1) yt-dlp로 기본 정보 + 자막
        print("  📥 yt-dlp로 영상 정보 및 자막 추출 중...")
        data = fetch_with_ytdlp(args.url, lang=args.lang)
        print(f"  ✅ 영상: {data['info']['title']}")

        sub_len = len(data.get("subtitles_text", ""))
        if sub_len > 0:
            print(f"  ✅ 자막 추출 완료 ({sub_len:,}자, 언어: {data.get('subtitle_lang', 'N/A')})")
        else:
            print("  ⚠️ 자막을 찾을 수 없습니다")

        # 2) YouTube API로 추가 메타데이터 (키 있을 때만)
        api_data = {}
        if args.api_key:
            print("  🔑 YouTube Data API로 상세 정보 조회 중...")
            api_data = fetch_with_youtube_api(video_id, args.api_key)
            if api_data:
                print(f"  ✅ API 데이터 수집 완료 (댓글: {format_number(api_data.get('comment_count', 0))})")
        else:
            print("  ℹ️ YouTube API 키 없음 — yt-dlp 데이터만 사용")
    except Exception as e:
        print(f"  ❌ 오류 발생: {e}")
        raise

    # 3) 마크다운 생성
    md_content = generate_markdown(data, api_data, args.url)

    # 4) 파일 저장
    output_path = Path(args.output_dir) if args.output_dir else Path("../05-Data-Inbox/Social")
    output_path.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'[\\/*?:"<>|]', "", data["info"]["title"])[:60]
    filename = f"{today}-YT-{safe_title}.md"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n📝 노트 저장: {filepath}")

    # JSON (선택)
    if args.json:
        json_path = output_path / f"{today}-YT-{video_id}.json"
        all_data = {"ytdlp": data, "api": api_data}
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"📄 JSON 저장: {json_path}")


if __name__ == "__main__":
    main()
