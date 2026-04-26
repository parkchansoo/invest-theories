#!/usr/bin/env python3
"""
SEC EDGAR 공시 원문 수집 스크립트
사용법:
  python fetch_sec.py <ticker> [--type 10-K] [--limit 5] [--output-dir <path>]

예시:
  python fetch_sec.py AAPL                        # 최근 공시 전체
  python fetch_sec.py NVDA --type 10-K --limit 3  # 연간 보고서 3건
  python fetch_sec.py TSLA --type 10-Q            # 분기 보고서
  python fetch_sec.py MSFT --type 8-K             # 수시 공시

주요 공시 유형:
  10-K  : 연간 보고서 (가장 상세)
  10-Q  : 분기 보고서
  8-K   : 수시 공시 (중요 사건 발생 시)
  S-1   : IPO 등록 서류
  DEF 14A: 주주총회 위임장
  4     : 내부자 거래 보고
  13F   : 기관투자자 보유 현황

※ SEC EDGAR는 API 키 없이 무료로 사용 가능합니다.
※ SEC 정책상 User-Agent에 이메일을 포함해야 합니다.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("필수 패키지를 설치하세요: pip install requests beautifulsoup4")
    sys.exit(1)


# ─── 설정 ───────────────────────────────────────────────
# SEC 정책: User-Agent에 회사명과 이메일 포함 필수
USER_AGENT = os.environ.get(
    "SEC_USER_AGENT",
    "StockResearch/1.0 (research@example.com)"
)
EDGAR_BASE = "https://efts.sec.gov/LATEST"
EDGAR_FILING_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"
EDGAR_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"
HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}
# ─────────────────────────────────────────────────────────


def get_cik(ticker: str) -> str:
    """티커로 CIK(Central Index Key)를 조회합니다."""
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        ticker_upper = ticker.upper()
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker_upper:
                cik = str(entry["cik_str"])
                return cik.zfill(10)  # CIK는 10자리 패딩
    return ""


def get_company_info(cik: str) -> dict:
    """CIK로 회사 정보를 조회합니다."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        return {
            "name": data.get("name", ""),
            "cik": cik,
            "ticker": data.get("tickers", [""])[0] if data.get("tickers") else "",
            "sic": data.get("sic", ""),
            "sic_description": data.get("sicDescription", ""),
            "fiscal_year_end": data.get("fiscalYearEnd", ""),
            "state": data.get("addresses", {}).get("business", {}).get("stateOrCountry", ""),
        }
    return {}


def search_filings(cik: str, form_type: str = None, limit: int = 10) -> list:
    """EDGAR에서 공시 목록을 검색합니다."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code != 200:
        return []

    data = resp.json()
    recent = data.get("filings", {}).get("recent", {})

    if not recent:
        return []

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    doc_names = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])

    filings = []
    for i in range(len(forms)):
        if form_type and forms[i] != form_type:
            continue
        filings.append({
            "form": forms[i],
            "filing_date": dates[i],
            "accession_number": accessions[i],
            "primary_document": doc_names[i] if i < len(doc_names) else "",
            "description": descriptions[i] if i < len(descriptions) else "",
        })
        if len(filings) >= limit:
            break

    return filings


def fetch_filing_text(cik: str, accession_number: str, primary_document: str) -> str:
    """공시 원문을 다운로드하고 텍스트로 변환합니다."""
    # accession number 포맷: 0000000000-00-000000 → 0000000000-00-000000
    acc_no_clean = accession_number.replace("-", "")

    # 원문 URL 구성
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_no_clean}/{primary_document}"

    try:
        time.sleep(0.15)  # SEC rate limit: 10 req/sec
        resp = requests.get(doc_url, headers=HEADERS, timeout=60)

        if resp.status_code != 200:
            # 대안 URL 시도
            doc_url_alt = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/{primary_document}"
            resp = requests.get(doc_url_alt, headers=HEADERS, timeout=60)

        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            if "html" in content_type or primary_document.endswith(".htm") or primary_document.endswith(".html"):
                return html_to_text(resp.text)
            else:
                return resp.text[:100000]
    except Exception as e:
        print(f"     ⚠️ 문서 다운로드 실패: {e}")

    return "(공시 원문을 가져올 수 없습니다)"


def html_to_text(html: str) -> str:
    """HTML을 정리된 텍스트로 변환합니다."""
    soup = BeautifulSoup(html, "lxml")

    # 불필요한 요소 제거
    for tag in soup(["script", "style", "meta", "link", "head"]):
        tag.decompose()

    # 테이블 처리 (재무제표 등)
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if rows:
            table_text = "\n"
            for row in rows:
                cells = row.find_all(["td", "th"])
                cell_texts = [c.get_text(strip=True) for c in cells]
                if any(cell_texts):  # 빈 행 건너뛰기
                    table_text += " | ".join(cell_texts) + "\n"
            table.replace_with(table_text)

    text = soup.get_text()

    # 연속 빈 줄 정리
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


def generate_filing_markdown(company: dict, filing: dict, full_text: str) -> str:
    """공시 노트를 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d")
    ticker = company.get("ticker", "")
    name = company.get("name", "")
    form = filing.get("form", "")
    filing_date = filing.get("filing_date", "")
    accession = filing.get("accession_number", "")
    description = filing.get("description", form)

    # SEC 뷰어 URL
    acc_no_clean = accession.replace("-", "")
    cik_clean = company.get("cik", "").lstrip("0")
    sec_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_no_clean}/{filing.get('primary_document', '')}"
    sec_index = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={form}&dateb=&owner=include&count=40"

    # 본문 전문 보존 (세부 내용 확인 가능하도록 원문 그대로 저장)
    text_preview = full_text if full_text else "(본문을 가져올 수 없습니다)"

    md = f"""---
ticker: "{ticker}"
company: "{name}"
form_type: "{form}"
filing_date: "{filing_date}"
accession_number: "{accession}"
collected: "{today}"
tags:
  - 공시
  - SEC
  - {ticker}
  - {form}
---

# {name} ({ticker}) — {form} ({filing_date})

## 공시 정보

| 항목 | 내용 |
|------|------|
| **기업명** | {name} ({ticker}) |
| **공시 유형** | {form} — {description} |
| **제출일** | {filing_date} |
| **Accession #** | {accession} |
| **SEC 원문** | [원문 보기]({sec_url}) |
| **EDGAR** | [검색 페이지]({sec_index}) |

## 요약 (5줄)
> (Claude에게 요약 요청 — 예: "이 공시 5줄로 요약해줘")

1.
2.
3.
4.
5.

---

## 공시 원문

> 아래는 SEC filing 원문을 그대로 추출한 전문입니다.

{text_preview}

---

## 투자 관련 시사점
>

## 관련 노트
-
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="SEC EDGAR 공시 원문 수집")
    parser.add_argument("ticker", help="종목 티커 (예: AAPL, NVDA)")
    parser.add_argument("--type", default=None, dest="form_type",
                        help="공시 유형 (10-K, 10-Q, 8-K, S-1, DEF 14A 등)")
    parser.add_argument("--limit", type=int, default=5, help="최대 검색 수")
    parser.add_argument("--no-text", action="store_true", help="원문 추출 생략 (목록만)")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    ticker = args.ticker.upper()

    # 출력 디렉토리
    output_path = Path(args.output_dir) if args.output_dir else Path("../05-Data-Inbox/Filings")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1) CIK 조회
    print(f"🔍 {ticker} CIK 조회 중...")
    cik = get_cik(ticker)
    if not cik:
        print(f"  ❌ '{ticker}'에 해당하는 CIK를 찾을 수 없습니다.")
        sys.exit(1)
    print(f"  ✅ CIK: {cik}")

    # 2) 회사 정보
    company = get_company_info(cik)
    print(f"  ✅ {company.get('name', ticker)} ({company.get('sic_description', '')})")

    # 3) 공시 검색
    type_str = args.form_type or "전체"
    print(f"\n📋 공시 검색: {type_str} (최대 {args.limit}건)")
    filings = search_filings(cik, form_type=args.form_type, limit=args.limit)

    if not filings:
        print("  ❌ 검색 결과가 없습니다.")
        sys.exit(1)

    print(f"  ✅ {len(filings)}건 발견\n")

    for i, f in enumerate(filings):
        print(f"  {i+1}. [{f['filing_date']}] {f['form']} — {f.get('description', '')}")

    # 4) 원문 수집 및 노트 생성
    print()
    for i, filing in enumerate(filings):
        form = filing["form"]
        date = filing["filing_date"]
        print(f"  📄 [{i+1}/{len(filings)}] {form} ({date}) 수집 중...")

        full_text = ""
        if not args.no_text:
            full_text = fetch_filing_text(cik, filing["accession_number"], filing["primary_document"])
            print(f"     ✅ 원문 수집 ({len(full_text):,}자)")
        else:
            print(f"     ℹ️ 원문 생략")

        md_content = generate_filing_markdown(company, filing, full_text)

        def clean_company_name(name):
            """회사명에서 법인 접미사 제거 및 파일명 안전 문자로 변환"""
            for suffix in [", Inc.", " Inc.", " Inc", " Corporation", " Corp.",
                           " Corp", " Ltd.", " Ltd", " plc", " PLC",
                           " Co.", " Co", " Company", " Technologies",
                           " Holdings", " Group", " and Chemicals",
                           " S.A.", " SE", " N.V.", " AG"]:
                name = name.replace(suffix, "")
            name = name.strip().replace(" ", "").replace(",", "").replace(".", "")
            name = name.replace("/", "-").replace("\\", "-")
            return name

        company_short = clean_company_name(company.get("name", ticker))
        safe_form = form.replace("/", "-")
        filename = f"{date}-SEC-{ticker}-{company_short}-{safe_form}.md"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f_out:
            f_out.write(md_content)
        print(f"     📝 저장: {filepath}")

        time.sleep(0.2)  # SEC rate limit 준수

    print(f"\n✅ 완료! {len(filings)}건의 SEC 공시 노트를 저장했습니다.")


if __name__ == "__main__":
    main()
