#!/usr/bin/env python3
"""
실적 데이터 수집 스크립트 - Yahoo Finance 기반
사용법: python fetch_earnings.py <ticker> [--output-dir <path>]

예시:
  python fetch_earnings.py AAPL
  python fetch_earnings.py NVDA --output-dir ../05-Data-Inbox/Earnings/
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("yfinance가 설치되지 않았습니다. pip install yfinance")
    sys.exit(1)


def fetch_earnings_data(ticker_symbol: str) -> dict:
    """실적 관련 데이터를 수집합니다."""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    data = {
        "ticker": ticker_symbol,
        "company": info.get("longName") or info.get("shortName", ticker_symbol),
        "currency": info.get("currency", "USD"),
    }

    # 분기별 재무제표
    try:
        qf = ticker.quarterly_financials
        if qf is not None and not qf.empty:
            data["quarterly"] = []
            for col in qf.columns[:4]:
                period = col.strftime("%Y-%m")
                q_data = {}
                for row in qf.index:
                    val = qf.loc[row, col]
                    q_data[row] = int(val) if val == val else None
                data["quarterly"].append({"period": period, "data": q_data})
    except Exception:
        pass

    # 실적 히스토리 (EPS 서프라이즈)
    try:
        eh = ticker.earnings_history
        if eh is not None and not eh.empty:
            data["earnings_history"] = []
            for _, row in eh.iterrows():
                data["earnings_history"].append({
                    "date": str(row.get("Earnings Date", "")),
                    "eps_estimate": row.get("EPS Estimate"),
                    "eps_actual": row.get("Reported EPS"),
                    "surprise_pct": row.get("Surprise(%)"),
                })
    except Exception:
        pass

    # 다음 실적 발표일
    try:
        cal = ticker.calendar
        if cal is not None:
            if isinstance(cal, dict):
                data["next_earnings"] = str(cal.get("Earnings Date", ["N/A"])[0]) if cal.get("Earnings Date") else "N/A"
            else:
                data["next_earnings"] = "N/A"
    except Exception:
        data["next_earnings"] = "N/A"

    return data


def format_big_number(num, currency="USD"):
    """큰 숫자를 읽기 쉽게 포맷"""
    if num is None:
        return "N/A"
    if currency == "KRW":
        if abs(num) >= 1e12:
            return f"{num/1e12:.1f}조"
        if abs(num) >= 1e8:
            return f"{num/1e8:,.0f}억"
        return f"{num:,.0f}"
    else:
        if abs(num) >= 1e9:
            return f"${num/1e9:.2f}B"
        if abs(num) >= 1e6:
            return f"${num/1e6:.1f}M"
        return f"${num:,.0f}"


def generate_earnings_markdown(data: dict) -> str:
    """실적 정리 마크다운을 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d")
    currency = data.get("currency", "USD")

    md = f"""---
ticker: "{data['ticker']}"
company: "{data['company']}"
date: "{today}"
tags:
  - 실적
  - {data['ticker']}
---

# {data['company']} ({data['ticker']}) — 실적 요약

> 자동 수집일: {today} | 출처: Yahoo Finance

"""

    # 분기별 실적 테이블
    quarterly = data.get("quarterly", [])
    if quarterly:
        md += "## 분기별 주요 실적\n\n"
        periods = [q["period"] for q in quarterly]
        md += "| 항목 | " + " | ".join(periods) + " |\n"
        md += "|------|" + "|".join(["---"] * len(periods)) + "|\n"

        key_items = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "EBITDA"]
        for item in key_items:
            row = f"| **{item}** |"
            for q in quarterly:
                val = q["data"].get(item)
                row += f" {format_big_number(val, currency)} |"
            md += row + "\n"
        md += "\n"

    # EPS 서프라이즈 히스토리
    eps_hist = data.get("earnings_history", [])
    if eps_hist:
        md += "## EPS 서프라이즈 히스토리\n\n"
        md += "| 발표일 | EPS 예상 | EPS 실적 | 서프라이즈 |\n"
        md += "|--------|----------|----------|----------|\n"
        for e in eps_hist[:8]:
            surprise = f"{e['surprise_pct']:.1f}%" if e.get('surprise_pct') is not None else "N/A"
            est = f"{e['eps_estimate']:.2f}" if e.get('eps_estimate') is not None else "N/A"
            actual = f"{e['eps_actual']:.2f}" if e.get('eps_actual') is not None else "N/A"
            md += f"| {e['date']} | {est} | {actual} | {surprise} |\n"
        md += "\n"

    # 다음 실적
    md += f"## 다음 실적 발표\n- **예정일**: {data.get('next_earnings', 'N/A')}\n\n"

    md += """## 내 해석
> 이 실적이 내 투자 논리에 미치는 영향

-

## 액션 아이템
- [ ] 종목 분석 노트 업데이트
- [ ] 목표가 재조정 필요 여부 확인
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="실적 데이터 수집")
    parser.add_argument("ticker", help="종목 티커")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    print(f"📊 {args.ticker} 실적 데이터 수집 중...")
    data = fetch_earnings_data(args.ticker)
    print(f"✅ {data['company']} 실적 수집 완료")

    md_content = generate_earnings_markdown(data)

    output_path = Path(args.output_dir) if args.output_dir else Path("../05-Data-Inbox/Earnings")
    output_path.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

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

    company_short = clean_company_name(data["company"])
    filepath = output_path / f"{today}-{args.ticker}-{company_short}-실적.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"📝 실적 노트 저장: {filepath}")


if __name__ == "__main__":
    main()
