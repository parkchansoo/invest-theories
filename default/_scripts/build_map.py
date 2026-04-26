#!/usr/bin/env python3
"""
옵시디언 볼트의 키워드/의미 맵을 자동 생성합니다.
볼트 내 모든 .md 파일을 스캔하여:
  1) 키워드 인덱스 (단어 → 관련 노트 목록)
  2) 주제별 MOC (Map of Content)
  3) 종목별 연결 맵
을 07-Maps/ 폴더에 마크다운으로 생성합니다.

사용법:
  python build_map.py [--vault-dir <path>]

Cowork에서: "맵 업데이트해줘" 라고 요청하면 됩니다.
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ─── 설정 ───────────────────────────────────────────────
# 무시할 폴더
IGNORE_DIRS = {".obsidian", "_scripts", "Templates", "07-Maps", "node_modules", ".git"}

# 투자 관련 핵심 키워드 카테고리
KEYWORD_CATEGORIES = {
    "반도체": ["반도체", "semiconductor", "HBM", "DRAM", "NAND", "파운드리", "foundry", "EUV",
               "패키징", "TSM", "ASML", "웨이퍼", "메모리", "GPU", "NPU", "AI칩"],
    "AI": ["AI", "인공지능", "LLM", "GPT", "머신러닝", "딥러닝", "생성형", "에이전트",
           "트랜스포머", "추론", "학습", "데이터센터", "클라우드"],
    "전기차/배터리": ["전기차", "EV", "배터리", "리튬", "양극재", "음극재", "전해질",
                    "충전", "자율주행", "테슬라", "BYD", "CATL"],
    "매크로/금리": ["금리", "인플레이션", "CPI", "PCE", "연준", "Fed", "FOMC", "기준금리",
                  "국채", "채권", "환율", "달러", "원화", "GDP", "고용", "실업률"],
    "밸류에이션": ["PER", "PBR", "PSR", "EV/EBITDA", "DCF", "FCF", "ROE", "ROA",
                 "영업이익률", "순이익률", "배당", "자사주", "밸류에이션"],
    "실적": ["실적", "매출", "영업이익", "순이익", "EPS", "가이던스", "컨센서스",
            "서프라이즈", "분기보고서", "사업보고서", "10-K", "10-Q"],
    "에너지": ["원유", "천연가스", "태양광", "풍력", "수소", "원전", "SMR", "에너지"],
    "헬륨/산업가스": ["헬륨", "helium", "산업가스", "industrial gas", "Linde", "Air Products",
                    "Air Liquide", "Nippon Sanso", "헬륨프리", "MRI", "극저온", "cryogenic",
                    "카타르", "Qatar", "Ras Laffan", "공급위기", "재활용", "재포집"],
    "우주/방산": ["우주", "방산", "NASA", "SpaceX", "로켓", "위성", "Redwire", "방위산업",
                 "아르테미스", "Artemis", "극초음속", "미사일"],
    "금융": ["은행", "증권", "보험", "핀테크", "결제", "대출", "예금", "금리차"],
    "바이오/헬스케어": ["바이오", "제약", "신약", "임상", "FDA", "GLP-1", "비만치료제",
                     "mRNA", "유전자", "의료기기"],
    "플랫폼/인터넷": ["플랫폼", "광고", "이커머스", "구독", "SaaS", "핀테크",
                    "메타", "구글", "아마존", "네이버", "카카오"],
}

# 종목 티커 패턴
TICKER_PATTERNS = [
    r"\b([A-Z]{2,5})\b",  # 미국 티커 (2-5 대문자)
    r"\b(\d{6})\b",        # 한국 종목코드 (6자리)
]
# ─────────────────────────────────────────────────────────


def scan_vault(vault_dir: Path) -> list:
    """볼트 내 모든 .md 파일을 스캔합니다."""
    notes = []
    for md_file in vault_dir.rglob("*.md"):
        # 무시 폴더 체크
        rel = md_file.relative_to(vault_dir)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # YAML frontmatter 파싱
        meta = {}
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                yaml_block = content[3:end]
                for line in yaml_block.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"').strip("'")

        notes.append({
            "path": str(rel),
            "name": md_file.stem,
            "folder": str(rel.parent),
            "meta": meta,
            "content": content,
            "size": len(content),
        })

    return notes


def extract_keywords(notes: list) -> dict:
    """각 노트에서 키워드 카테고리를 매칭합니다."""
    keyword_map = defaultdict(list)  # category → [note_info, ...]

    for note in notes:
        text = note["content"].lower()
        matched_categories = set()

        for category, keywords in KEYWORD_CATEGORIES.items():
            for kw in keywords:
                if kw.lower() in text:
                    matched_categories.add(category)
                    break

        for cat in matched_categories:
            keyword_map[cat].append({
                "name": note["name"],
                "path": note["path"],
                "folder": note["folder"],
                "date": note["meta"].get("date") or note["meta"].get("created")
                        or note["meta"].get("collected") or note["meta"].get("filing_date", ""),
            })

    return dict(keyword_map)


def extract_tickers(notes: list) -> dict:
    """노트에서 종목 티커/코드를 추출합니다."""
    # 이미 알려진 티커 (frontmatter에서)
    ticker_map = defaultdict(list)  # ticker → [note_info, ...]

    for note in notes:
        tickers = set()

        # frontmatter에서 티커 추출
        if note["meta"].get("ticker"):
            tickers.add(note["meta"]["ticker"])

        # 본문에서 $TICKER 패턴 또는 태그에서 추출
        content = note["content"]
        # [[종목명]] 링크에서 추출
        wiki_links = re.findall(r"\[\[([^\]]+)\]\]", content)
        for link in wiki_links:
            # Watchlist 폴더의 노트를 참조하는 경우
            if any(market in link for market in ["01-Watchlist", "KR/", "US/", "Global/"]):
                tickers.add(link.split("/")[-1])

        for t in tickers:
            if t and len(t) >= 2:
                ticker_map[t].append({
                    "name": note["name"],
                    "path": note["path"],
                    "folder": note["folder"],
                })

    return dict(ticker_map)


def extract_topics(notes: list) -> dict:
    """Data-Inbox의 주제 폴더별 노트를 정리합니다."""
    topic_map = defaultdict(list)

    for note in notes:
        folder = note["folder"]
        if folder.startswith("05-Data-Inbox/"):
            topic = folder.replace("05-Data-Inbox/", "").split("/")[0]
            if topic and topic != "_미분류":
                topic_map[topic].append({
                    "name": note["name"],
                    "path": note["path"],
                    "date": note["meta"].get("date") or note["meta"].get("collected", ""),
                    "source": note["meta"].get("source", ""),
                })

    return dict(topic_map)


def generate_keyword_map(keyword_map: dict, vault_dir: Path):
    """키워드 인덱스 MOC를 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""---
updated: "{today}"
tags:
  - MOC
  - 키워드맵
---

# 키워드 맵

> 자동 생성: {today}
> 볼트의 모든 노트를 스캔하여 투자 주제별로 분류한 인덱스입니다.
> `_scripts/build_map.py` 를 실행하거나 "맵 업데이트해줘"로 갱신할 수 있습니다.

"""

    # 카테고리별 정렬 (노트 수 많은 순)
    sorted_cats = sorted(keyword_map.items(), key=lambda x: len(x[1]), reverse=True)

    for category, note_list in sorted_cats:
        md += f"## {category} ({len(note_list)})\n\n"
        # 날짜 역순 정렬
        sorted_notes = sorted(note_list, key=lambda x: x.get("date", ""), reverse=True)
        for n in sorted_notes:
            date_str = f" `{n['date']}`" if n.get("date") else ""
            md += f"- [[{n['name']}]]{date_str} — {n['folder']}\n"
        md += "\n"

    # 미매칭 노트
    all_matched = set()
    for notes in keyword_map.values():
        for n in notes:
            all_matched.add(n["path"])

    map_path = vault_dir / "07-Maps" / "키워드맵.md"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(md, encoding="utf-8")
    print(f"  📝 키워드맵 저장: {map_path}")


def generate_topic_map(topic_map: dict, vault_dir: Path):
    """주제별 MOC를 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = f"""---
updated: "{today}"
tags:
  - MOC
  - 주제맵
---

# 주제별 소스 맵

> 자동 생성: {today}
> Data-Inbox의 주제별 폴더 구조와 소스 목록입니다.

"""

    for topic, note_list in sorted(topic_map.items()):
        md += f"## {topic} ({len(note_list)})\n\n"
        sorted_notes = sorted(note_list, key=lambda x: x.get("date", ""), reverse=True)
        for n in sorted_notes:
            date_str = f"`{n['date']}`" if n.get("date") else ""
            source = f"[{n['source']}]" if n.get("source") else ""
            md += f"- [[{n['name']}]] {date_str} {source}\n"
        md += "\n"

    if not topic_map:
        md += "(아직 주제별로 분류된 소스가 없습니다)\n\n"

    map_path = vault_dir / "07-Maps" / "주제맵.md"
    map_path.write_text(md, encoding="utf-8")
    print(f"  📝 주제맵 저장: {map_path}")


def build_ticker_company_lookup(notes: list) -> dict:
    """종목 노트에서 ticker → company 이름 매핑을 생성합니다.
    파일명(note["name"])도 키로 추가하여 wikilink 표시명으로 활용."""
    lookup = {}
    for note in notes:
        meta = note["meta"]
        ticker = meta.get("ticker", "")
        company = meta.get("company", "")
        if ticker and company:
            # 한국 종목의 경우 .KS/.KQ 접미사 제거
            clean_ticker = ticker.replace(".KS", "").replace(".KQ", "")
            lookup[clean_ticker] = company
            lookup[ticker] = company
            # 파일명도 매핑 (예: "005930-삼성전자" → "삼성전자")
            lookup[note["name"]] = company
    return lookup


def generate_ticker_map(ticker_map: dict, vault_dir: Path, ticker_company: dict = None):
    """종목 연결 맵을 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    if ticker_company is None:
        ticker_company = {}

    md = f"""---
updated: "{today}"
tags:
  - MOC
  - 종목맵
---

# 종목 연결 맵

> 자동 생성: {today}
> 각 종목이 언급된 모든 노트의 연결 관계입니다.

"""

    for ticker, note_list in sorted(ticker_map.items()):
        if len(note_list) < 1:
            continue
        company = ticker_company.get(ticker, "")
        heading = f"{company} ({ticker})" if company else ticker
        md += f"## {heading} ({len(note_list)})\n\n"
        for n in note_list:
            # 종목 노트 자체는 회사명으로 표시
            display = ticker_company.get(n["name"], n["name"])
            md += f"- [[{n['name']}|{display}]] — {n['folder']}\n"
        md += "\n"

    if not ticker_map:
        md += "(아직 종목이 등록되지 않았습니다. Watchlist에 종목을 추가하면 여기에 나타납니다)\n\n"

    map_path = vault_dir / "07-Maps" / "종목맵.md"
    map_path.write_text(md, encoding="utf-8")
    print(f"  📝 종목맵 저장: {map_path}")


def generate_recent_activity(notes: list, vault_dir: Path):
    """최근 활동 타임라인을 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 날짜가 있는 노트들을 모아서 최신순 정렬
    dated_notes = []
    for note in notes:
        date = (note["meta"].get("date") or note["meta"].get("created")
                or note["meta"].get("collected") or note["meta"].get("filing_date", ""))
        if date:
            dated_notes.append({
                "name": note["name"],
                "path": note["path"],
                "folder": note["folder"],
                "date": date,
                "tags": note["meta"].get("tags", ""),
            })

    dated_notes.sort(key=lambda x: x["date"], reverse=True)

    md = f"""---
updated: "{today}"
tags:
  - MOC
  - 타임라인
---

# 최근 활동

> 자동 생성: {today}
> 날짜가 있는 모든 노트를 최신순으로 보여줍니다.

"""

    current_date = ""
    for n in dated_notes[:50]:  # 최근 50건
        d = n["date"][:10]  # YYYY-MM-DD
        if d != current_date:
            current_date = d
            md += f"\n### {d}\n\n"
        md += f"- [[{n['name']}]] — {n['folder']}\n"

    map_path = vault_dir / "07-Maps" / "최근활동.md"
    map_path.write_text(md, encoding="utf-8")
    print(f"  📝 최근활동 저장: {map_path}")


def generate_dashboard(notes: list, vault_dir: Path):
    """대시보드(Home.md)를 볼트 현황에 맞게 자동 갱신합니다."""
    today = datetime.now().strftime("%Y-%m-%d")

    # ── 관심종목 수집 ──
    watchlist_kr = []
    watchlist_us = []
    watchlist_global = []
    for note in notes:
        folder = note["folder"]
        meta = note["meta"]
        status = meta.get("status", "")
        if folder == "01-Watchlist/KR":
            watchlist_kr.append({"name": note["name"], "status": status,
                                 "company": meta.get("company", note["name"])})
        elif folder == "01-Watchlist/US":
            watchlist_us.append({"name": note["name"], "status": status,
                                 "company": meta.get("company", note["name"])})
        elif folder == "01-Watchlist/Global":
            watchlist_global.append({"name": note["name"], "status": status,
                                     "company": meta.get("company", note["name"])})

    # ── 진행 중인 아이디어 수집 ──
    ideas = []
    for note in notes:
        if note["folder"] == "03-Ideas/Active":
            meta = note["meta"]
            # tickers 파싱 (YAML에서 문자열로 넘어옴)
            tickers_raw = meta.get("tickers", "")
            if isinstance(tickers_raw, str):
                tickers_raw = tickers_raw.strip("[]").replace('"', '').replace("'", "")
                tickers_list = [t.strip() for t in tickers_raw.split(",") if t.strip()]
            else:
                tickers_list = []
            ideas.append({
                "name": note["name"],
                "title": meta.get("title", note["name"]),
                "conviction": meta.get("conviction", ""),
                "status": meta.get("status", ""),
                "tickers": ", ".join(tickers_list[:5]),
            })

    # ── 최근 매매 수집 ──
    trades = []
    for note in notes:
        if note["folder"] == "04-Trading-Journal" and note["name"] != "Portfolio-Summary":
            meta = note["meta"]
            # 복기 노트는 제외
            if "복기" in note["name"]:
                continue
            trades.append({
                "name": note["name"],
                "date": meta.get("date", ""),
                "ticker": meta.get("ticker", ""),
                "company": meta.get("company", ""),
                "action": meta.get("action", ""),
            })
    trades.sort(key=lambda x: x.get("date", ""), reverse=True)

    # ── 대시보드 마크다운 생성 ──
    md = f"""---
tags:
  - dashboard
---

# 투자 대시보드

> 마지막 업데이트: {today} (자동 갱신 — `build_map.py`)

---

## 진행 중인 투자 아이디어

> `03-Ideas/Active` 폴더의 아이디어들

"""
    if ideas:
        md += "| 아이디어 | 확신도 | 상태 | 관련 종목 |\n"
        md += "|----------|--------|------|-----------|\n"
        for idea in ideas:
            md += f"| [[{idea['name']}\\|{idea['title']}]] | {idea['conviction']} | {idea['status']} | {idea['tickers']} |\n"
    else:
        md += "(아직 진행 중인 아이디어가 없습니다)\n"

    md += """
---

## 관심 종목 (Watchlist)

"""
    # 한국
    if watchlist_kr:
        md += "### 한국\n"
        md += "| 종목 | 상태 |\n"
        md += "|------|------|\n"
        for w in sorted(watchlist_kr, key=lambda x: x["company"]):
            md += f"| [[{w['name']}\\|{w['company']}]] | `{w['status']}` |\n"
        md += "\n"

    # 미국
    if watchlist_us:
        md += "### 미국\n"
        md += "| 종목 | 상태 |\n"
        md += "|------|------|\n"
        for w in sorted(watchlist_us, key=lambda x: x["company"]):
            md += f"| [[{w['name']}\\|{w['company']}]] | `{w['status']}` |\n"
        md += "\n"

    # 글로벌
    if watchlist_global:
        md += "### 글로벌\n"
        md += "| 종목 | 상태 |\n"
        md += "|------|------|\n"
        for w in sorted(watchlist_global, key=lambda x: x["company"]):
            md += f"| [[{w['name']}\\|{w['company']}]] | `{w['status']}` |\n"
        md += "\n"

    if not (watchlist_kr or watchlist_us or watchlist_global):
        md += "(아직 관심종목이 없습니다)\n\n"

    md += """---

## 최근 매매

"""
    if trades:
        md += "| 날짜 | 종목 | 매수/매도 | 매매일지 |\n"
        md += "|------|------|-----------|----------|\n"
        for t in trades[:10]:  # 최근 10건
            md += f"| {t['date']} | {t['company']} ({t['ticker']}) | {t['action']} | [[{t['name']}]] |\n"
    else:
        md += "(아직 매매 기록이 없습니다)\n"

    md += """
---

## 이번 주 할 일

- [ ] 관심종목 주간 시세 체크
- [ ] 주요 실적 발표 일정 확인
- [ ] 매매일지 복기
- [ ] 새로운 아이디어 리서치

---

## 맵 & 인덱스

볼트의 모든 노트를 키워드·주제·종목별로 자동 분류한 맵입니다.
"맵 업데이트해줘"로 갱신할 수 있습니다.

- [[키워드맵]] — 반도체, AI, 매크로 등 투자 주제별 노트 인덱스
- [[주제맵]] — Data-Inbox 주제 폴더별 소스 목록
- [[종목맵]] — 각 종목이 언급된 모든 노트 연결
- [[최근활동]] — 날짜순 타임라인 (최근 50건)

---

## 빠른 링크

- [[Portfolio-Summary|포트폴리오 현황]]
- 관심종목: [[01-Watchlist/KR|한국]] | [[01-Watchlist/US|미국]]
- [[03-Ideas/Active|진행중 아이디어]] | [[03-Ideas/Archive|보관 아이디어]]
- [[04-Trading-Journal|매매일지]]
- [[05-Data-Inbox|데이터 수집함]] — 주제별 폴더로 자동 분류

---

## Cowork 활용법

이 볼트는 Cowork(Claude)와 함께 사용하도록 설계되었습니다. 대화를 나누면서 소스를 수집하고, 생각을 정리하고, 투자 아이디어로 발전시켜 가세요.

**소스 수집 (원문 전문 저장)**
- "이 유튜브 영상 스크립트 가져와줘: https://youtube.com/watch?v=..."
- "삼성전자 최근 사업보고서 가져와줘"
- "NVDA 10-K 공시 가져와서 정리해줘"

**종목 분석**
- "NVDA 종목분석 노트 만들어줘"
- "반도체 대장주들 비교해줘 (NVDA, AMD, INTC, AVGO)"
- "삼성전자 최근 실적 정리해줘"

**아이디어 & 매매 기록**
- "지금 나눈 대화 내용을 투자 아이디어로 정리해줘"
- "오늘 매수한 AAPL 매매일지 작성해줘"

**맵 갱신**
- "맵 업데이트해줘" — 키워드맵, 주제맵, 종목맵, 최근활동, 대시보드 일괄 갱신
"""

    home_path = vault_dir / "00-Dashboard" / "Home.md"
    home_path.parent.mkdir(parents=True, exist_ok=True)
    home_path.write_text(md, encoding="utf-8")
    print(f"  📝 대시보드 저장: {home_path}")


def main():
    parser = argparse.ArgumentParser(description="옵시디언 볼트 키워드/의미 맵 생성")
    parser.add_argument("--vault-dir", default=None, help="볼트 루트 디렉토리")
    args = parser.parse_args()

    vault_dir = Path(args.vault_dir) if args.vault_dir else Path(__file__).parent.parent
    print(f"🗺️  볼트 스캔 중: {vault_dir}")

    # 1) 전체 노트 스캔
    notes = scan_vault(vault_dir)
    print(f"  ✅ {len(notes)}개 노트 발견")

    # 2) 키워드 인덱스 생성
    keyword_map = extract_keywords(notes)
    print(f"  ✅ {len(keyword_map)}개 키워드 카테고리 매칭")

    # 3) 주제 맵 생성
    topic_map = extract_topics(notes)

    # 4) 종목 맵 생성
    ticker_map = extract_tickers(notes)
    print(f"  ✅ {len(ticker_map)}개 종목 발견")

    # 5) 종목명 매핑 생성
    ticker_company = build_ticker_company_lookup(notes)

    # 6) 맵 파일 생성
    print("\n📝 맵 생성 중...")
    generate_keyword_map(keyword_map, vault_dir)
    generate_topic_map(topic_map, vault_dir)
    generate_ticker_map(ticker_map, vault_dir, ticker_company)
    generate_recent_activity(notes, vault_dir)
    generate_dashboard(notes, vault_dir)

    print(f"\n✅ 맵 및 대시보드 생성 완료! 07-Maps/ 및 00-Dashboard/를 확인하세요.")


if __name__ == "__main__":
    main()
