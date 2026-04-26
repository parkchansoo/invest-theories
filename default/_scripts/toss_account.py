#!/usr/bin/env python3
"""
토스증권 계좌 조회 스크립트
- 로컬(tossctl 있는 환경): tossctl CLI로 조회
- Cowork(tossctl 없는 환경): 세션 파일로 API 직접 호출

사용법:
  python toss_account.py positions [--market us|kr|all] [--save]
  python toss_account.py summary
  python toss_account.py orders [--market us|kr|all] [--save]
  python toss_account.py quote NVDA GOOGL 005930 [--json]
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# tossctl 존재 여부로 모드 결정
HAS_TOSSCTL = shutil.which("tossctl") is not None


def get_client():
    """API 클라이언트 반환. tossctl 없으면 직접 API 클라이언트 사용."""
    if HAS_TOSSCTL:
        return None  # subprocess 방식
    # toss_api.py 임포트
    sys.path.insert(0, str(SCRIPT_DIR))
    from toss_api import TossClient
    return TossClient()


def run_tossctl(*args) -> dict | str:
    """tossctl CLI 호출 (로컬 전용)."""
    import subprocess
    cmd = ["tossctl"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"[ERROR] tossctl 실패: {' '.join(cmd)}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        output = result.stdout.strip()
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output
    except subprocess.TimeoutExpired:
        print("[ERROR] tossctl 타임아웃 (30초)", file=sys.stderr)
        sys.exit(1)


# ──────────────────────────────────────────────
# 마크다운 포맷터
# ──────────────────────────────────────────────

def format_positions_md(data, market: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "---",
        f"date: {today}",
        "type: portfolio-snapshot",
        f"market: {market}",
        "tags: [포트폴리오, 토스증권]",
        "---",
        "",
        f"# 포트폴리오 스냅샷 ({today})",
        "",
    ]

    if isinstance(data, str):
        lines.append(data)
        return "\n".join(lines)

    lines.append("| 종목 | 티커 | 수량 | 평균단가 | 현재가 | 평가금액 | 수익률 |")
    lines.append("|------|------|------|----------|--------|----------|--------|")

    # cert-api 응답에서 SORTED_OVERVIEW 섹션의 종목 추출
    positions = []
    if isinstance(data, dict):
        sections = data.get("result", {}).get("sections", [])
        for section in sections:
            if section.get("type") == "SORTED_OVERVIEW":
                for product in section.get("data", {}).get("products", []):
                    positions.extend(product.get("items", []))
        if not positions:
            # fallback: 다른 구조
            positions = data.get("positions") or data.get("data") or []
    elif isinstance(data, list):
        positions = data

    for pos in positions:
        name = pos.get("stockName", "")
        symbol = pos.get("stockSymbol") or pos.get("stockCode", "")
        qty = pos.get("quantity", "")
        # 가격은 dict 형태 {krw: ..., usd: ...}
        purchase = pos.get("purchasePrice", {})
        current = pos.get("currentPrice", {})
        evaluated = pos.get("evaluatedAmount", {})
        pnl_rate = pos.get("profitLossRate", {})

        if isinstance(purchase, dict):
            avg = purchase.get("usd") or purchase.get("krw", "")
        else:
            avg = purchase
        if isinstance(current, dict):
            cur = current.get("usd") or current.get("krw", "")
        else:
            cur = current
        if isinstance(evaluated, dict):
            val = evaluated.get("usd") or evaluated.get("krw", "")
        else:
            val = evaluated
        if isinstance(pnl_rate, dict):
            pnl = pnl_rate.get("usd") or pnl_rate.get("krw", "")
            if isinstance(pnl, (int, float)):
                pnl = f"{pnl:.2%}"
        else:
            pnl = pnl_rate

        if qty:  # 수량 0인 항목 제외
            qty_int = int(qty) if isinstance(qty, float) and qty == int(qty) else qty
            lines.append(f"| {name} | {symbol} | {qty_int} | {avg} | {cur} | {val} | {pnl} |")

    return "\n".join(lines)


def format_orders_md(data, market: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "---",
        f"date: {today}",
        "type: order-history",
        f"market: {market}",
        "tags: [체결내역, 토스증권]",
        "---",
        "",
        f"# 체결 내역 ({today})",
        "",
        "| 일시 | 종목 | 매매 | 수량 | 단가 | 금액 | 상태 |",
        "|------|------|------|------|------|------|------|",
    ]

    orders = data if isinstance(data, list) else []
    if isinstance(data, dict):
        orders = data.get("orders") or data.get("data") or data.get("result", {}).get("orders", [])
        if not isinstance(orders, list):
            orders = []

    for o in orders:
        dt = o.get("date", o.get("executedAt", o.get("orderDate", "")))
        name = o.get("name", o.get("symbol", o.get("stockName", "")))
        side = o.get("side", o.get("action", o.get("orderType", "")))
        qty = o.get("quantity", o.get("qty", o.get("executedQuantity", "")))
        price = o.get("price", o.get("executedPrice", ""))
        amount = o.get("amount", o.get("total", o.get("executedAmount", "")))
        status = o.get("status", "")
        lines.append(f"| {dt} | {name} | {side} | {qty} | {price} | {amount} | {status} |")

    return "\n".join(lines)


def save_note(md: str, label: str):
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = SCRIPT_DIR.parent / "04-Trading-Journal"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}-{label}.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"\n[SAVED] {out_path}")


# ──────────────────────────────────────────────
# 서브커맨드
# ──────────────────────────────────────────────

def cmd_positions(args):
    print(f"[INFO] 포지션 조회 중... (market={args.market})")

    if HAS_TOSSCTL:
        data = run_tossctl("portfolio", "positions")
    else:
        client = get_client()
        data = client.positions()

    print(json.dumps(data, indent=2, ensure_ascii=False))

    md = format_positions_md(data, args.market)
    if args.save:
        save_note(md, "포트폴리오-스냅샷")

    if args.md:
        print("\n" + md)


def cmd_summary(args):
    print("[INFO] 계좌 요약 조회 중...")

    if HAS_TOSSCTL:
        data = run_tossctl("account", "summary")
    else:
        client = get_client()
        data = client.summary()

    print(json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, dict) else data)


def cmd_orders(args):
    print(f"[INFO] 체결 내역 조회 중... (market={args.market})")

    if HAS_TOSSCTL:
        data = run_tossctl("orders", "completed", "--market", args.market)
    else:
        client = get_client()
        data = client.orders(market=args.market)

    print(json.dumps(data, indent=2, ensure_ascii=False))

    md = format_orders_md(data, args.market)
    if args.save:
        save_note(md, f"체결내역-{args.market}")

    if args.md:
        print("\n" + md)


def cmd_quote(args):
    """종목 시세 조회. 토스증권 API 사용."""
    client = get_client()
    if client is None:
        # tossctl 환경이어도 시세 조회는 API 직접 호출
        sys.path.insert(0, str(SCRIPT_DIR))
        from toss_api import TossClient
        client = TossClient()

    tickers = args.tickers

    if args.json:
        prices = client.watchlist_prices(tickers)
        print(json.dumps(prices, indent=2, ensure_ascii=False))
        return

    # 테이블 출력
    prices = client.watchlist_prices(tickers)

    # KR / US 분리
    kr_items = [p for p in prices if p.get("currency") == "KRW"]
    us_items = [p for p in prices if p.get("currency") != "KRW" and "error" not in p]
    err_items = [p for p in prices if "error" in p]

    if kr_items:
        print("\n📌 한국 종목")
        print(f"{'종목':<16} {'현재가':>12} {'전일대비':>10} {'등락률':>8} {'고가':>12} {'저가':>12} {'거래량':>14}")
        print("-" * 90)
        for p in kr_items:
            close = p["close"]
            change = p["change"]
            pct = p["change_pct"]
            sign = "+" if change >= 0 else ""
            arrow = "🔺" if change > 0 else ("🔻" if change < 0 else "➖")
            name = p.get("name", p["ticker"])
            print(f"{arrow} {name:<14} {close:>12,.0f}원 {sign}{change:>9,.0f} {sign}{pct:>6.1f}% {p['high']:>12,.0f} {p['low']:>12,.0f} {p['volume']:>14,}")

    if us_items:
        print("\n📌 미국 종목")
        print(f"{'종목':<8} {'종목명':<14} {'현재가':>12} {'원화':>10} {'전일대비':>10} {'등락률':>8} {'고가':>12} {'저가':>12} {'거래량':>14}")
        print("-" * 110)
        for p in us_items:
            close = p["close"]
            change = p["change"]
            pct = p["change_pct"]
            sign = "+" if change >= 0 else ""
            arrow = "🔺" if change > 0 else ("🔻" if change < 0 else "➖")
            name = p.get("name", p["ticker"])
            krw = p.get("close_krw")
            krw_str = f"₩{krw:,.0f}" if krw else "-"
            print(f"{arrow} {p['ticker']:<6} {name:<12} ${close:>10,.2f} {krw_str:>10} {sign}{change:>8,.2f} {sign}{pct:>6.1f}% ${p['high']:>10,.2f} ${p['low']:>10,.2f} {p['volume']:>14,}")

    if err_items:
        print("\n⚠️ 조회 실패")
        for p in err_items:
            print(f"  {p['ticker']}: {p['error']}")

    # 환율
    try:
        fx = client.exchange_rate()
        rate = fx.get("result", {}).get("baseExchangeRate", 0)
        if rate:
            print(f"\n💱 USD/KRW 환율: {rate:,.2f}")
    except Exception:
        pass


def main():
    mode = "tossctl" if HAS_TOSSCTL else "API 직접호출"
    parser = argparse.ArgumentParser(
        description=f"토스증권 계좌 조회 (모드: {mode})"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pos = sub.add_parser("positions", help="포지션 조회")
    p_pos.add_argument("--market", default="all", choices=["us", "kr", "all"])
    p_pos.add_argument("--save", action="store_true", help="노트로 저장")
    p_pos.add_argument("--md", action="store_true", help="마크다운 테이블 출력")
    p_pos.set_defaults(func=cmd_positions)

    p_sum = sub.add_parser("summary", help="계좌 요약")
    p_sum.set_defaults(func=cmd_summary)

    p_ord = sub.add_parser("orders", help="체결 내역")
    p_ord.add_argument("--market", default="all", choices=["us", "kr", "all"])
    p_ord.add_argument("--save", action="store_true", help="노트로 저장")
    p_ord.add_argument("--md", action="store_true", help="마크다운 테이블 출력")
    p_ord.set_defaults(func=cmd_orders)

    p_quote = sub.add_parser("quote", help="종목 시세 조회")
    p_quote.add_argument("tickers", nargs="+", help="티커 목록 (예: NVDA GOOGL 005930)")
    p_quote.add_argument("--json", action="store_true", help="JSON 출력")
    p_quote.set_defaults(func=cmd_quote)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
