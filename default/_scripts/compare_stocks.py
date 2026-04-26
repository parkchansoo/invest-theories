#!/usr/bin/env python3
"""
종목 비교 스크립트 - 여러 종목의 핵심 지표를 비교 테이블로 생성
사용법: python compare_stocks.py AAPL MSFT GOOGL NVDA [--output-dir <path>]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("yfinance가 설치되지 않았습니다.")
    sys.exit(1)


def fetch_comparison_data(tickers: list) -> list:
    """여러 종목의 비교 데이터를 수집합니다."""
    results = []
    for t in tickers:
        print(f"  📊 {t} 수집 중...")
        try:
            ticker = yf.Ticker(t)
            info = ticker.info
            results.append({
                "ticker": t,
                "company": info.get("shortName", t),
                "market_cap": info.get("marketCap"),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "revenue_growth": info.get("revenueGrowth"),
                "operating_margins": info.get("operatingMargins"),
                "profit_margins": info.get("profitMargins"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "dividend_yield": info.get("dividendYield"),
                "free_cashflow": info.get("freeCashflow"),
                "recommendation": info.get("recommendationKey"),
                "target_mean": info.get("targetMeanPrice"),
            })
        except Exception as e:
            print(f"  ❌ {t} 실패: {e}")
            results.append({"ticker": t, "error": str(e)})
    return results


def fmt(val, fmt_type="ratio"):
    """값 포맷"""
    if val is None:
        return "N/A"
    if isinstance(val, float) and val != val:
        return "N/A"
    if fmt_type == "ratio":
        return f"{val:.2f}"
    elif fmt_type == "pct":
        return f"{val*100:.1f}%" if abs(val) < 1 else f"{val:.1f}%"
    elif fmt_type == "mcap":
        if val >= 1e12:
            return f"${val/1e12:.1f}T"
        if val >= 1e9:
            return f"${val/1e9:.0f}B"
        return f"${val/1e6:.0f}M"
    elif fmt_type == "price":
        return f"${val:,.2f}"
    return str(val)


def generate_comparison_markdown(results: list, title: str = None) -> str:
    """비교 마크다운을 생성합니다."""
    today = datetime.now().strftime("%Y-%m-%d")
    tickers_str = ", ".join([r["ticker"] for r in results if "error" not in r])

    md = f"""---
date: "{today}"
tags:
  - 종목비교
---

# 종목 비교: {title or tickers_str}

> 자동 수집일: {today} | 출처: Yahoo Finance

## 기본 정보

| | """ + " | ".join([f"**{r.get('company', r['ticker'])}**<br/>({r['ticker']})" for r in results if "error" not in r]) + """ |
|---|""" + "|".join(["---"] * len([r for r in results if "error" not in r])) + """|
"""

    valid = [r for r in results if "error" not in r]

    rows = [
        ("기업명", "company", None),
        ("시가총액", "market_cap", "mcap"),
        ("현재가", "current_price", "price"),
        ("PER (TTM)", "trailing_pe", "ratio"),
        ("PER (Fwd)", "forward_pe", "ratio"),
        ("PBR", "pb_ratio", "ratio"),
        ("PSR", "ps_ratio", "ratio"),
        ("EV/EBITDA", "ev_ebitda", "ratio"),
        ("매출성장률", "revenue_growth", "pct"),
        ("영업이익률", "operating_margins", "pct"),
        ("순이익률", "profit_margins", "pct"),
        ("ROE", "roe", "pct"),
        ("부채비율", "debt_to_equity", "ratio"),
        ("배당수익률", "dividend_yield", "pct"),
        ("애널리스트", "recommendation", None),
        ("목표가(평균)", "target_mean", "price"),
    ]

    for label, key, fmt_type in rows:
        row = f"| **{label}** |"
        for r in valid:
            val = r.get(key)
            if fmt_type:
                row += f" {fmt(val, fmt_type)} |"
            else:
                row += f" {val or 'N/A'} |"
        md += row + "\n"

    md += """
## 분석 메모
>

## 결론
-
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="종목 비교")
    parser.add_argument("tickers", nargs="+", help="비교할 종목들")
    parser.add_argument("--title", default=None, help="비교 제목")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    print(f"📊 종목 비교: {', '.join(args.tickers)}")
    results = fetch_comparison_data(args.tickers)

    md = generate_comparison_markdown(results, args.title)

    output_path = Path(args.output_dir) if args.output_dir else Path("../02-Research/Sector")
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

    # 파일명에 회사명 포함 (최대 3개)
    valid_results = [r for r in results if "error" not in r]
    name_parts = []
    for r in valid_results[:3]:
        company_short = clean_company_name(r.get("company", r["ticker"]))
        name_parts.append(f"{r['ticker']}-{company_short}")
    if len(valid_results) > 3:
        name_parts.append(f"외{len(valid_results)-3}종목")
    tickers_str = "-vs-".join(name_parts)
    filepath = output_path / f"{today}-비교-{tickers_str}.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"📝 비교 노트 저장: {filepath}")


if __name__ == "__main__":
    main()
