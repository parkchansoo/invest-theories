#!/usr/bin/env python3
"""
토스증권 매매 스크립트
- 로컬(tossctl 있는 환경): tossctl CLI의 6단계 안전장치 적용
- Cowork(tossctl 없는 환경): 세션 파일로 API 직접 호출

사용법:
  python toss_trade.py preview --symbol NVDA --side buy --qty 10 --price 130
  python toss_trade.py execute --symbol NVDA --side buy --qty 10 --price 130
  python toss_trade.py status
  python toss_trade.py cancel --order-date 2026-03-22 --order-no 12345

⚠️ execute는 실제 자금이 움직입니다. 반드시 preview 먼저 확인하세요.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
HAS_TOSSCTL = shutil.which("tossctl") is not None

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"


def get_client():
    sys.path.insert(0, str(SCRIPT_DIR))
    from toss_api import TossClient
    return TossClient()


def run_tossctl(*args, timeout=30) -> dict | str:
    cmd = ["tossctl"] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            print(f"{RED}[ERROR] tossctl 실패: {' '.join(cmd)}{RESET}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return {"error": result.stderr.strip()}
        output = result.stdout.strip()
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output
    except subprocess.TimeoutExpired:
        print(f"{RED}[ERROR] tossctl 타임아웃 ({timeout}초){RESET}", file=sys.stderr)
        sys.exit(1)


def generate_trade_journal(symbol: str, side: str, qty: str, price: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    action = "매수" if side == "buy" else "매도"
    return f"""---
date: "{today}"
ticker: "{symbol}"
company: ""
action: "{action}"
idea: ""
result: ""
pnl_pct: ""
tags:
  - 매매일지
  - {action}
  - {symbol}
source: tossctl
---

# {today} | {action} | {symbol}

## 매매 정보

| 항목 | 내용 |
|------|------|
| **매매 유형** | {action} |
| **수량** | {qty} |
| **단가** | {price} |
| **총 금액** | |
| **수수료** | |
| **계좌** | 토스증권 |

## 연결
- **투자 아이디어**: <!-- [[아이디어-노트명]] -->
- **종목 노트**: <!-- [[{symbol}]] -->

## 매매 근거
> 왜 이 시점에 이 가격으로 매매했는가?

-

## 심리 상태
> 매매 당시 감정 상태 (확신/불안/FOMO/공포 등)

-

## 매매 후 체크리스트
- [ ] 포트폴리오 비중 확인
- [ ] 손절/익절 라인 설정
- [ ] 관련 종목 노트 업데이트

## 복기 (매매 후 1주일 뒤 작성)
- **결과** (수익/손실/보유중):
- **thesis 검증**:
- **타이밍 평가**:
- **심리 편향**:
- **배운 점**:
- **다음에 다르게 할 것**:
"""


# ──────────────────────────────────────────────
# 서브커맨드
# ──────────────────────────────────────────────

def cmd_preview(args):
    action = "매수" if args.side == "buy" else "매도"
    print(f"{GREEN}[PREVIEW] 주문 시뮬레이션 — 실제 체결되지 않습니다{RESET}")
    print(f"  종목: {args.symbol}")
    print(f"  방향: {action}")
    print(f"  수량: {args.qty}")
    print(f"  가격: {args.price}")
    print()

    if HAS_TOSSCTL:
        result = run_tossctl(
            "order", "preview",
            "--symbol", args.symbol,
            "--side", args.side,
            "--qty", str(args.qty),
            "--price", str(args.price),
        )
    else:
        client = get_client()
        result = client.order_preview(args.symbol, args.side, args.qty, args.price)

    if isinstance(result, dict) and "error" in result:
        print(f"{RED}미리보기 실패: {result['error']}{RESET}")
        return

    print(f"{GREEN}=== 주문 미리보기 결과 ==={RESET}")
    print(json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else result)


def cmd_execute(args):
    action = "매수" if args.side == "buy" else "매도"

    print(f"\n{RED}{BOLD}{'='*50}")
    print(f"  ⚠️  실제 주문 실행 요청")
    print(f"{'='*50}{RESET}")
    print(f"  종목: {BOLD}{args.symbol}{RESET}")
    print(f"  방향: {BOLD}{action}{RESET}")
    print(f"  수량: {BOLD}{args.qty}{RESET}")
    print(f"  가격: {BOLD}{args.price}{RESET}")
    print()

    # 1단계: 미리보기
    print(f"{YELLOW}[1/2] 주문 미리보기 실행 중...{RESET}")
    if HAS_TOSSCTL:
        preview = run_tossctl(
            "order", "preview",
            "--symbol", args.symbol,
            "--side", args.side,
            "--qty", str(args.qty),
            "--price", str(args.price),
        )
    else:
        client = get_client()
        preview = client.order_preview(args.symbol, args.side, args.qty, args.price)

    if isinstance(preview, dict) and "error" in preview:
        print(f"{RED}미리보기 실패 — 주문 중단: {preview['error']}{RESET}")
        return

    print(f"{GREEN}미리보기 결과:{RESET}")
    print(json.dumps(preview, indent=2, ensure_ascii=False) if isinstance(preview, dict) else preview)

    # 2단계: 실행
    # preview에서 orderKey 추출
    order_key = None
    if isinstance(preview, dict):
        result_data = preview.get("result", preview)
        order_key = result_data.get("orderKey")

    print(f"\n{YELLOW}[2/2] 주문 실행 중...{RESET}")

    if HAS_TOSSCTL:
        # tossctl은 자체 6단계 안전장치 적용
        perm = run_tossctl("order", "permissions", "grant", "--ttl", "300")
        if isinstance(perm, dict) and "error" in perm:
            print(f"{RED}권한 부여 실패: {perm['error']}{RESET}")
            return
        confirm_token = perm.get("token", perm.get("confirm", "")) if isinstance(perm, dict) else ""

        exec_args = [
            "order", "place",
            "--symbol", args.symbol, "--side", args.side,
            "--qty", str(args.qty), "--price", str(args.price),
            "--execute", "--dangerously-skip-permissions",
        ]
        if confirm_token:
            exec_args.extend(["--confirm", confirm_token])
        result = run_tossctl(*exec_args, timeout=60)
    else:
        client = get_client()
        result = client.order_place(
            args.symbol, args.side, args.qty, int(args.price),
            order_key=order_key, close=int(args.price)
        )

    if isinstance(result, dict) and "error" in result:
        print(f"{RED}주문 실행 실패: {result['error']}{RESET}")
        return

    print(f"\n{GREEN}{BOLD}✅ 주문 실행 완료{RESET}")
    print(json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else result)

    # 매매일지 생성
    if args.journal:
        journal_md = generate_trade_journal(args.symbol, args.side, str(args.qty), str(args.price))
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = SCRIPT_DIR.parent / "04-Trading-Journal"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{today}-{action}-{args.symbol}.md"
        out_path.write_text(journal_md, encoding="utf-8")
        print(f"\n{GREEN}[SAVED] 매매일지: {out_path}{RESET}")


def cmd_status(args):
    print("[INFO] 미체결 주문 조회 중...")
    if HAS_TOSSCTL:
        result = run_tossctl("orders", "list")
    else:
        client = get_client()
        result = client.pending_orders()
    print(json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else result)


def cmd_cancel(args):
    print(f"{YELLOW}[INFO] 주문 취소 중...{RESET}")
    if HAS_TOSSCTL:
        result = run_tossctl("order", "cancel", "--id", f"{args.order_date}/{args.order_no}")
    else:
        client = get_client()
        result = client.order_cancel(args.order_date, args.order_no)
    print(json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else result)


def main():
    mode = "tossctl" if HAS_TOSSCTL else "API 직접호출"
    parser = argparse.ArgumentParser(
        description=f"토스증권 매매 (모드: {mode}) — 주의: 실제 자금이 움직입니다"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_prev = sub.add_parser("preview", help="주문 미리보기 (체결 없음)")
    p_prev.add_argument("--symbol", required=True)
    p_prev.add_argument("--side", required=True, choices=["buy", "sell"])
    p_prev.add_argument("--qty", required=True, type=int)
    p_prev.add_argument("--price", required=True)
    p_prev.set_defaults(func=cmd_preview)

    p_exec = sub.add_parser("execute", help="주문 실행 (실제 체결)")
    p_exec.add_argument("--symbol", required=True)
    p_exec.add_argument("--side", required=True, choices=["buy", "sell"])
    p_exec.add_argument("--qty", required=True, type=int)
    p_exec.add_argument("--price", required=True)
    p_exec.add_argument("--journal", action="store_true", default=True)
    p_exec.add_argument("--no-journal", dest="journal", action="store_false")
    p_exec.set_defaults(func=cmd_execute)

    p_status = sub.add_parser("status", help="미체결 주문 조회")
    p_status.set_defaults(func=cmd_status)

    p_cancel = sub.add_parser("cancel", help="주문 취소")
    p_cancel.add_argument("--order-date", required=True, help="주문일 (YYYY-MM-DD)")
    p_cancel.add_argument("--order-no", required=True, help="주문번호")
    p_cancel.set_defaults(func=cmd_cancel)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
