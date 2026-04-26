#!/usr/bin/env python3
"""
주식 데이터 수집 스크립트 - Yahoo Finance 기반
사용법: python fetch_stock.py <ticker> [--market KR|US|Global] [--output-dir <path>]

예시:
  python fetch_stock.py AAPL --market US
  python fetch_stock.py 005930.KS --market KR
  python fetch_stock.py NVDA --market US --output-dir ../01-Watchlist/US/
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("yfinance가 설치되지 않았습니다. pip install yfinance 로 설치하세요.")
    sys.exit(1)


def fetch_stock_data(ticker_symbol: str) -> dict:
    """Yahoo Finance에서 종목 데이터를 가져옵니다."""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info

    # 기본 정보
    data = {
        "ticker": ticker_symbol,
        "company": info.get("longName") or info.get("shortName", ticker_symbol),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "country": info.get("country", "N/A"),
        "currency": info.get("currency", "N/A"),
        "exchange": info.get("exchange", "N/A"),
        "website": info.get("website", ""),
        "description": info.get("longBusinessSummary", ""),
    }

    # 시세 정보
    data["price"] = {
        "current": info.get("currentPrice") or info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "open": info.get("regularMarketOpen"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "50d_avg": info.get("fiftyDayAverage"),
        "200d_avg": info.get("twoHundredDayAverage"),
    }

    # 밸류에이션
    data["valuation"] = {
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "pb_ratio": info.get("priceToBook"),
        "ps_ratio": info.get("priceToSalesTrailing12Months"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "ev_revenue": info.get("enterpriseToRevenue"),
    }

    # 재무 지표
    data["financials"] = {
        "revenue": info.get("totalRevenue"),
        "revenue_growth": info.get("revenueGrowth"),
        "gross_margins": info.get("grossMargins"),
        "operating_margins": info.get("operatingMargins"),
        "profit_margins": info.get("profitMargins"),
        "ebitda": info.get("ebitda"),
        "net_income": info.get("netIncomeToCommon"),
        "eps_trailing": info.get("trailingEps"),
        "eps_forward": info.get("forwardEps"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "free_cashflow": info.get("freeCashflow"),
        "operating_cashflow": info.get("operatingCashflow"),
    }

    # 배당
    data["dividend"] = {
        "dividend_rate": info.get("dividendRate"),
        "dividend_yield": info.get("dividendYield"),
        "payout_ratio": info.get("payoutRatio"),
        "ex_dividend_date": info.get("exDividendDate"),
    }

    # 주가 히스토리 (최근 6개월)
    hist = ticker.history(period="6mo")
    if not hist.empty:
        data["price_history_6m"] = {
            "start_price": round(float(hist["Close"].iloc[0]), 2),
            "end_price": round(float(hist["Close"].iloc[-1]), 2),
            "high": round(float(hist["High"].max()), 2),
            "low": round(float(hist["Low"].min()), 2),
            "avg_volume": int(hist["Volume"].mean()),
            "return_pct": round(
                (float(hist["Close"].iloc[-1]) / float(hist["Close"].iloc[0]) - 1)
                * 100,
                2,
            ),
        }

    # 분기 실적
    try:
        quarterly = ticker.quarterly_financials
        if quarterly is not None and not quarterly.empty:
            cols = quarterly.columns[:4]  # 최근 4분기
            data["quarterly_revenue"] = {}
            data["quarterly_net_income"] = {}
            for col in cols:
                period = col.strftime("%Y-%m")
                if "Total Revenue" in quarterly.index:
                    val = quarterly.loc["Total Revenue", col]
                    data["quarterly_revenue"][period] = (
                        int(val) if val == val else None
                    )
                if "Net Income" in quarterly.index:
                    val = quarterly.loc["Net Income", col]
                    data["quarterly_net_income"][period] = (
                        int(val) if val == val else None
                    )
    except Exception:
        pass

    # 애널리스트 추천
    data["analyst"] = {
        "target_high": info.get("targetHighPrice"),
        "target_low": info.get("targetLowPrice"),
        "target_mean": info.get("targetMeanPrice"),
        "target_median": info.get("targetMedianPrice"),
        "recommendation": info.get("recommendationKey"),
        "num_analysts": info.get("numberOfAnalystOpinions"),
    }

    return data


def format_number(num, currency="USD"):
    """숫자를 읽기 쉬운 형태로 포맷합니다."""
    if num is None:
        return "N/A"
    if isinstance(num, float) and num != num:  # NaN check
        return "N/A"

    if currency == "KRW":
        if abs(num) >= 1e12:
            return f"{num/1e12:.1f}조원"
        elif abs(num) >= 1e8:
            return f"{num/1e8:.0f}억원"
        elif abs(num) >= 1e4:
            return f"{num/1e4:.0f}만원"
        return f"{num:,.0f}원"
    else:
        if abs(num) >= 1e12:
            return f"${num/1e12:.2f}T"
        elif abs(num) >= 1e9:
            return f"${num/1e9:.2f}B"
        elif abs(num) >= 1e6:
            return f"${num/1e6:.1f}M"
        return f"${num:,.0f}"


def format_pct(num):
    """퍼센트 포맷"""
    if num is None:
        return "N/A"
    if isinstance(num, float) and num != num:
        return "N/A"
    if abs(num) < 1:  # 0.15 -> 15%
        return f"{num*100:.1f}%"
    return f"{num:.1f}%"


def format_ratio(num):
    """비율 포맷"""
    if num is None:
        return "N/A"
    if isinstance(num, float) and num != num:
        return "N/A"
    return f"{num:.2f}"


def generate_markdown(data: dict, market: str) -> str:
    """종목 분석 마크다운 노트를 생성합니다."""
    currency = "KRW" if market == "KR" else data.get("currency", "USD")
    fn = format_number
    today = datetime.now().strftime("%Y-%m-%d")

    # 가격 포맷
    price = data["price"]["current"]
    price_str = f"{price:,.0f}원" if currency == "KRW" else f"${price:,.2f}" if price else "N/A"

    # aliases 생성
    ticker_clean = data['ticker'].replace('.KS', '').replace('.KQ', '')
    if market == "KR":
        aliases_str = f'aliases: [{data["company"]}]'
    else:
        aliases_str = f'aliases: [{data["company"]}, {ticker_clean}]'

    # 차트 링크 생성
    if market == "KR":
        chart_links = (
            f"- [네이버 금융](https://finance.naver.com/item/main.naver?code={ticker_clean})"
            f" | [Yahoo Finance](https://finance.yahoo.com/quote/{data['ticker']})"
            f" | [TradingView](https://www.tradingview.com/symbols/KRX-{ticker_clean}/)"
        )
    else:
        chart_links = (
            f"- [Yahoo Finance](https://finance.yahoo.com/quote/{ticker_clean})"
            f" | [TradingView](https://www.tradingview.com/symbols/{ticker_clean}/)"
        )

    md = f"""---
ticker: "{data['ticker']}"
company: "{data['company']}"
market: "{market}"
sector: "{data['sector']}"
industry: "{data['industry']}"
created: "{today}"
updated: "{today}"
status: "monitoring"
{aliases_str}
tags:
  - 종목분석
  - {market}
  - {data['sector'].replace(' ', '-') if data['sector'] != 'N/A' else 'Uncategorized'}
---

# {data['company']} ({ticker_clean})

## 차트 & 시세 링크
{chart_links}

## 기업 개요
- **섹터/산업**: {data['sector']} / {data['industry']}
- **국가**: {data['country']}
- **시가총액**: {fn(data['valuation']['market_cap'], currency)}
- **통화**: {data['currency']}
- **거래소**: {data['exchange']}
- **웹사이트**: {data['website']}

> {data['description'][:500] + '...' if len(data.get('description', '')) > 500 else data.get('description', '')}

## 현재 시세 ({today})
- **현재가**: {price_str}
- **52주 최고/최저**: {fn(data['price']['52w_high'], currency)} / {fn(data['price']['52w_low'], currency)}
- **50일 이평**: {fn(data['price']['50d_avg'], currency)}
- **200일 이평**: {fn(data['price']['200d_avg'], currency)}

## 핵심 재무 지표

| 지표 | 값 |
|------|-----|
| **매출** | {fn(data['financials']['revenue'], currency)} |
| **매출성장률** | {format_pct(data['financials']['revenue_growth'])} |
| **영업이익률** | {format_pct(data['financials']['operating_margins'])} |
| **순이익률** | {format_pct(data['financials']['profit_margins'])} |
| **EBITDA** | {fn(data['financials']['ebitda'], currency)} |
| **EPS (TTM)** | {format_ratio(data['financials']['eps_trailing'])} |
| **EPS (Forward)** | {format_ratio(data['financials']['eps_forward'])} |
| **ROE** | {format_pct(data['financials']['roe'])} |
| **ROA** | {format_pct(data['financials']['roa'])} |
| **부채비율** | {format_ratio(data['financials']['debt_to_equity'])} |
| **유동비율** | {format_ratio(data['financials']['current_ratio'])} |
| **FCF** | {fn(data['financials']['free_cashflow'], currency)} |

## 밸류에이션

| 지표 | 값 |
|------|-----|
| **PER (TTM)** | {format_ratio(data['valuation']['trailing_pe'])} |
| **PER (Forward)** | {format_ratio(data['valuation']['forward_pe'])} |
| **PBR** | {format_ratio(data['valuation']['pb_ratio'])} |
| **PSR** | {format_ratio(data['valuation']['ps_ratio'])} |
| **EV/EBITDA** | {format_ratio(data['valuation']['ev_ebitda'])} |
| **EV/Revenue** | {format_ratio(data['valuation']['ev_revenue'])} |
| **PEG** | {format_ratio(data['valuation']['peg_ratio'])} |

## 배당
- **배당률**: {format_pct(data['dividend']['dividend_yield'])}
- **배당금**: {format_ratio(data['dividend']['dividend_rate'])}
- **배당성향**: {format_pct(data['dividend']['payout_ratio'])}

## 애널리스트 의견
- **추천**: {data['analyst']['recommendation'] or 'N/A'}
- **목표가 (평균)**: {fn(data['analyst']['target_mean'], currency)}
- **목표가 (범위)**: {fn(data['analyst']['target_low'], currency)} ~ {fn(data['analyst']['target_high'], currency)}
- **애널리스트 수**: {data['analyst']['num_analysts'] or 'N/A'}명
"""

    # 6개월 수익률
    hist = data.get("price_history_6m")
    if hist:
        md += f"""
## 최근 6개월 주가 요약
- **6개월 수익률**: {hist['return_pct']}%
- **기간 고점**: {fn(hist['high'], currency)}
- **기간 저점**: {fn(hist['low'], currency)}
- **평균 거래량**: {hist['avg_volume']:,}주
"""

    md += """
## 투자 포인트 (Bull Case)
1.
2.
3.

## 리스크 요인 (Bear Case)
1.
2.
3.

## 내 목표 가격
- **적정가**:
- **매수가**:
- **손절가**:
- **산출 근거**:

## 최근 이슈 / 뉴스
-

## 내 의견
>

## 관련 노트
-
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="Yahoo Finance 주식 데이터 수집")
    parser.add_argument("ticker", help="종목 티커 (예: AAPL, 005930.KS)")
    parser.add_argument("--market", default="US", choices=["KR", "US", "Global"])
    parser.add_argument("--output-dir", default=None, help="출력 디렉토리")
    parser.add_argument("--json", action="store_true", help="JSON으로도 출력")
    args = parser.parse_args()

    print(f"📊 {args.ticker} 데이터 수집 중...")
    data = fetch_stock_data(args.ticker)
    print(f"✅ {data['company']} 데이터 수집 완료")

    # 마크다운 생성
    md_content = generate_markdown(data, args.market)

    # 파일명 결정: {티커}-{회사명}.md
    # 한국: 005930-삼성전자.md, 미국: NVDA-NVIDIA.md
    ticker_clean = args.ticker.replace(".KS", "").replace(".KQ", "")

    def clean_company_name(name):
        """회사명에서 법인 접미사 제거 및 파일명 안전 문자로 변환"""
        for suffix in [", Inc.", " Inc.", " Inc", " Corporation", " Corp.",
                       " Corp", " Ltd.", " Ltd", " plc", " PLC",
                       " Co.", " Co", " Company", " Technologies",
                       " Holdings", " Group", " and Chemicals",
                       " S.A.", " SE", " N.V.", " AG"]:
            name = name.replace(suffix, "")
        # 파일명에 사용 불가한 문자 제거, 공백→없앰
        name = name.strip().replace(" ", "").replace(",", "").replace(".", "")
        name = name.replace("/", "-").replace("\\", "-")
        return name

    if args.market == "KR":
        # Yahoo는 한국 종목에 영문명을 반환하므로, shortName도 확인
        company_short = clean_company_name(data["company"])
        filename = f"{ticker_clean}-{company_short}.md"
    else:
        company_short = clean_company_name(data["company"])
        filename = f"{ticker_clean}-{company_short}.md"

    # 출력 디렉토리
    if args.output_dir:
        output_path = Path(args.output_dir)
    else:
        output_path = Path(f"../01-Watchlist/{args.market}")

    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"📝 노트 저장: {filepath}")

    # JSON 출력 (선택)
    if args.json:
        json_path = output_path / f"{args.ticker}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"📄 JSON 저장: {json_path}")

    return data


if __name__ == "__main__":
    main()
