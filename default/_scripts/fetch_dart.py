#!/usr/bin/env python3
"""
DART(전자공시시스템) 공시 원문 수집 스크립트
DART 웹사이트에서 직접 크롤링하므로 API 키가 필요 없습니다.

사용법:
  python fetch_dart.py <기업명> [--type 사업보고서] [--limit 5] [--output-dir <path>]

예시:
  python fetch_dart.py 삼성전자
  python fetch_dart.py SK하이닉스 --type 사업보고서 --limit 3
  python fetch_dart.py 카카오 --type 분기보고서
  python fetch_dart.py 삼성전자 --no-text          # 목록만 확인
"""

import argparse
import json
import re
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    print("필수 패키지를 설치하세요: pip install requests beautifulsoup4 lxml")
    sys.exit(1)


# ─── 설정 ───────────────────────────────────────────────
DART_WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://dart.fss.or.kr/dsab007/main.do",
    "X-Requested-With": "XMLHttpRequest",
}

# 공시 유형 → DART 검색 키워드
REPORT_NAMES = {
    "사업보고서": "사업보고서",
    "반기보고서": "반기보고서",
    "분기보고서": "분기보고서",
    "감사보고서": "감사보고서",
    "주요사항보고서": "주요사항보고서",
}
# ─────────────────────────────────────────────────────────


def search_filings(corp_name: str, report_type: str = None,
                   limit: int = 10, start_date: str = None) -> list:
    """DART 웹사이트에서 공시를 검색합니다."""
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")

    data = {
        "currentPage": "1",
        "maxResults": str(limit),
        "maxLinks": "5",
        "sort": "date",
        "series": "desc",
        "textCrpNm": corp_name,
        "startDate": start_date,
        "endDate": end_date,
    }

    if report_type and report_type in REPORT_NAMES:
        data["reportNamePopYn"] = "Y"
        data["reportName"] = REPORT_NAMES[report_type]

    url = "https://dart.fss.or.kr/dsab007/detailSearch.ax"
    resp = requests.post(url, data=data, headers=DART_WEB_HEADERS, timeout=15)

    if resp.status_code != 200:
        print(f"  ⚠️ DART 검색 실패 (HTTP {resp.status_code})")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table")
    if not table:
        return []

    filings = []
    rows = table.find_all("tr")[1:]  # 헤더 건너뛰기

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 5:
            continue

        # rcpNo 추출
        links = row.find_all("a")
        rcept_no = ""
        report_nm = ""
        for link in links:
            href = link.get("href", "")
            onclick = link.get("onclick", "")
            if "rcpNo=" in href:
                match = re.search(r"rcpNo=(\d+)", href)
                if match:
                    rcept_no = match.group(1)
                report_nm = link.get_text(strip=True)
            elif "openReportViewer" in onclick:
                match = re.search(r"openReportViewer\('(\d+)'", onclick)
                if match:
                    rcept_no = match.group(1)
                report_nm = link.get_text(strip=True)

        if not rcept_no:
            continue

        # 기업명에서 시장 표시 제거 (유=유가증권, 코=코스닥 등)
        raw_corp = tds[1].get_text(strip=True)
        clean_corp = re.sub(r"^[유코외기]", "", raw_corp)

        filing_date = tds[4].get_text(strip=True).replace(".", "-")

        filings.append({
            "rcept_no": rcept_no,
            "corp_name": clean_corp,
            "report_nm": report_nm,
            "filing_date": filing_date,
            "submitter": tds[3].get_text(strip=True),
        })

    return filings


def fetch_filing_document(rcept_no: str) -> str:
    """공시 원문(HTML)을 가져와 텍스트로 변환합니다."""
    viewer_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        resp = requests.get(viewer_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return "(공시 페이지 접근 실패)"

        # dcmNo 추출 — node1['dcmNo'] = "12345" 패턴 우선
        dcm_matches = re.findall(r"\['dcmNo'\]\s*=\s*\"(\d+)\"", resp.text)
        if not dcm_matches:
            dcm_matches = re.findall(r"dcmNo=(\d+)", resp.text)

        if not dcm_matches:
            return _extract_from_page(resp.text)

        # 가장 많이 등장하는 dcmNo 사용 (메인 문서)
        from collections import Counter
        dcm_no = Counter(dcm_matches).most_common(1)[0][0]

        # eleId=1부터 시도 (eleId=0은 빈 응답인 경우가 많음)
        for ele_id in [1, 0, 2]:
            doc_url = (
                f"https://dart.fss.or.kr/report/viewer.do?"
                f"rcpNo={rcept_no}&dcmNo={dcm_no}&eleId={ele_id}"
                f"&offset=0&length=0&dtd=dart3.xsd"
            )
            doc_resp = requests.get(doc_url, headers=headers, timeout=60)
            if doc_resp.status_code == 200 and len(doc_resp.text) > 500:
                return html_to_text(doc_resp.text)

    except Exception as e:
        print(f"     ⚠️ 문서 수집 오류: {e}")

    return "(공시 원문을 가져올 수 없습니다)"


def _extract_from_page(page_html: str) -> str:
    """뷰어 페이지에서 직접 텍스트를 추출합니다 (폴백)."""
    soup = BeautifulSoup(page_html, "lxml")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if src and ("viewer" in src or "report" in src):
            if not src.startswith("http"):
                src = f"https://dart.fss.or.kr{src}"
            try:
                resp = requests.get(src, headers=headers, timeout=30)
                if resp.status_code == 200:
                    return html_to_text(resp.text)
            except Exception:
                continue

    return "(공시 원문을 가져올 수 없습니다)"


def html_to_text(html: str) -> str:
    """HTML을 정리된 텍스트로 변환합니다."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    # 테이블 → 파이프 구분 텍스트
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if rows:
            table_text = "\n"
            for row in rows:
                cells = row.find_all(["td", "th"])
                cell_texts = [c.get_text(strip=True) for c in cells]
                if any(cell_texts):
                    table_text += " | ".join(cell_texts) + "\n"
            table.replace_with(table_text)

    text = soup.get_text()

    # 연속 빈 줄 정리 (최대 1줄)
    lines = []
    blank_count = 0
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            blank_count += 1
            if blank_count <= 1:
                lines.append("")
        else:
            blank_count = 0
            lines.append(line)

    return "\n".join(lines)


def generate_filing_markdown(filing: dict, full_text: str) -> str:
    """공시 노트를 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d")
    corp_name = filing.get("corp_name", "")
    report_nm = re.sub(r"[\s]+", " ", filing.get("report_nm", "")).strip()
    rcept_no = filing.get("rcept_no", "")
    filing_date = filing.get("filing_date", "")

    dart_url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
    text_content = full_text if full_text else "(본문을 가져올 수 없습니다)"

    md = f"""---
corp_name: "{corp_name}"
report_type: "{report_nm}"
filing_date: "{filing_date}"
rcept_no: "{rcept_no}"
collected: "{today}"
tags:
  - 공시
  - DART
  - {corp_name}
---

# {corp_name} — {report_nm}

## 공시 정보

| 항목 | 내용 |
|------|------|
| **기업명** | {corp_name} |
| **공시명** | {report_nm} |
| **접수일** | {filing_date} |
| **공시번호** | {rcept_no} |
| **DART 링크** | [{report_nm}]({dart_url}) |

## 요약 (5줄)
> (Claude에게 요약 요청 — 예: "이 공시 5줄로 요약해줘")

1.
2.
3.
4.
5.

---

## 공시 원문

> 아래는 DART 공시 원문을 그대로 추출한 전문입니다.

{text_content}

---

## 투자 관련 시사점
>

## 관련 노트
-
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="DART 공시 원문 수집 (API 키 불필요)")
    parser.add_argument("query", help="기업명 (예: 삼성전자, SK하이닉스)")
    parser.add_argument("--type", default=None, dest="report_type",
                        help="공시 유형 (사업보고서/반기보고서/분기보고서/감사보고서)")
    parser.add_argument("--limit", type=int, default=5, help="최대 검색 수")
    parser.add_argument("--no-text", action="store_true", help="원문 추출 생략 (목록만)")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    # 출력 디렉토리
    output_path = Path(args.output_dir) if args.output_dir else Path("../05-Data-Inbox/Filings")
    output_path.mkdir(parents=True, exist_ok=True)

    type_str = args.report_type or "전체"
    print(f"🔍 DART 공시 검색: {args.query} ({type_str}, 최대 {args.limit}건)")

    filings = search_filings(args.query, report_type=args.report_type, limit=args.limit)

    if not filings:
        print(f"  ❌ '{args.query}'에 대한 공시를 찾을 수 없습니다.")
        sys.exit(1)

    print(f"  ✅ {len(filings)}건 발견\n")
    for i, f in enumerate(filings):
        print(f"  {i+1}. [{f['filing_date']}] {f['report_nm']}")

    print()
    for i, filing in enumerate(filings):
        report_nm = filing["report_nm"]
        print(f"  📄 [{i+1}/{len(filings)}] {report_nm} 원문 수집 중...")

        full_text = ""
        if not args.no_text:
            full_text = fetch_filing_document(filing["rcept_no"])
            print(f"     ✅ 원문 수집 ({len(full_text):,}자)")
        else:
            print("     ℹ️ 원문 생략")

        md_content = generate_filing_markdown(filing, full_text)

        corp_name = filing["corp_name"]
        # 보고서명에서 줄바꿈/탭/특수문자 제거
        clean_nm = re.sub(r"[\s]+", " ", report_nm).strip()
        safe_name = re.sub(r'[\\/*?:"<>|]', "", clean_nm)[:40]
        filing_date = filing["filing_date"].replace(".", "-")
        filename = f"{filing_date}-DART-{corp_name}-{safe_name}.md"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f_out:
            f_out.write(md_content)
        print(f"     📝 저장: {filepath}")

    print(f"\n✅ 완료! {len(filings)}건의 공시 노트를 저장했습니다.")


if __name__ == "__main__":
    main()
