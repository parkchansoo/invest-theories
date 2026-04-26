"""
toss_api.py — 토스증권 API 직접 호출 모듈
tossctl 세션 파일을 읽어 Python에서 바로 API를 호출한다.
tossctl 바이너리가 없는 환경(Cowork VM 등)에서도 동작한다.

사용법 (모듈):
    from toss_api import TossClient
    client = TossClient()          # _trade-data/sessions/toss_session.json 자동 로드
    positions = client.positions()
    summary = client.summary()
    orders = client.orders(market="all")

    # 종목 검색 & 시세 조회
    results = client.search_stock("NVDA")
    price = client.stock_price("US19990122001")       # 토스 내부 코드
    price = client.stock_price_by_ticker("NVDA")      # 티커로 자동 변환
    prices = client.watchlist_prices(["NVDA", "GOOGL", "005930"])  # 다종목 시세
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from http.cookiejar import CookieJar

# ──────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────

API_BASE = "https://wts-api.tossinvest.com"
INFO_BASE = "https://wts-info-api.tossinvest.com"
CERT_BASE = "https://wts-cert-api.tossinvest.com"

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "_trade-data" / "sessions"
SESSION_PATH = DATA_DIR / "toss_session.json"

# ──────────────────────────────────────────────
# 세션 로더
# ──────────────────────────────────────────────


class SessionExpiredError(Exception):
    """세션이 만료되었을 때."""
    pass


class SessionNotFoundError(Exception):
    """세션 파일이 없을 때."""
    pass


def load_session(path: Path = SESSION_PATH) -> dict:
    """tossctl 세션 파일(JSON) 로드."""
    if not path.exists():
        raise SessionNotFoundError(
            f"세션 파일이 없습니다: {path}\n"
            f"로컬에서 먼저 실행하세요: cd default/_scripts && ./toss_sync.sh"
        )

    with open(path, "r", encoding="utf-8") as f:
        session = json.load(f)

    # 만료 체크
    expires = session.get("ExpiresAt") or session.get("expires_at")
    if expires:
        try:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if datetime.now(exp_dt.tzinfo) > exp_dt:
                raise SessionExpiredError(
                    "세션이 만료되었습니다.\n"
                    "로컬에서 tossctl auth login → ./toss_sync.sh를 다시 실행하세요."
                )
        except (ValueError, TypeError):
            pass  # 파싱 실패 시 무시

    return session


def build_headers(session: dict) -> dict:
    """세션에서 HTTP 헤더 구성."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://www.tossinvest.com/account",
        "Origin": "https://www.tossinvest.com",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }

    # 세션 헤더 복사 (Browser-Tab-Id, App-Version, X-XSRF-TOKEN 등)
    sess_headers = session.get("Headers") or session.get("headers") or {}
    for k, v in sess_headers.items():
        headers[k] = v

    return headers


def build_cookie_string(session: dict) -> str:
    """세션 쿠키 → Cookie 헤더 문자열."""
    cookies = session.get("Cookies") or session.get("cookies") or {}
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


# ──────────────────────────────────────────────
# API 클라이언트
# ──────────────────────────────────────────────


class TossClient:
    """토스증권 API 클라이언트."""

    def __init__(self, session_path: Path = SESSION_PATH):
        self._session = load_session(session_path)
        self._headers = build_headers(self._session)
        self._cookies = build_cookie_string(self._session)

    def _request(self, method: str, url: str, data: dict = None) -> dict:
        """HTTP 요청 실행."""
        headers = {**self._headers, "Cookie": self._cookies}
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"raw": raw}
        except HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8")
            except Exception:
                pass
            if e.code == 401:
                raise SessionExpiredError(
                    "인증 실패 (401). 세션이 만료되었습니다.\n"
                    "로컬에서 tossctl auth login → ./toss_sync.sh를 실행하세요."
                )
            raise RuntimeError(
                f"API 오류 {e.code}: {e.reason}\n{body_text}"
            )
        except URLError as e:
            raise RuntimeError(f"네트워크 오류: {e.reason}")

    def _get(self, path: str, base: str = API_BASE) -> dict:
        return self._request("GET", f"{base}{path}")

    def _post(self, path: str, data: dict = None, base: str = API_BASE) -> dict:
        return self._request("POST", f"{base}{path}", data)

    # ── 조회 API ──────────────────────────────

    def positions(self) -> dict:
        """포지션 조회 (cert-api 사용)."""
        return self._post("/api/v2/dashboard/asset/sections/all", data={}, base=CERT_BASE)

    def summary(self) -> dict:
        """계좌 요약."""
        return self._get("/api/v1/my-assets/summaries/markets/all/overview")

    def accounts(self) -> dict:
        """계좌 목록."""
        return self._get("/api/v1/account/list")

    def orders(self, market: str = "all", days: int = 90) -> dict:
        """체결 내역. market='all'이면 kr+us 합산 조회."""
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        markets = ["kr", "us"] if market == "all" else [market]
        all_body: list = []

        for m in markets:
            page = 1
            while True:
                path = (
                    f"/api/v2/trading/my-orders/markets/{m}/by-date/completed"
                    f"?range.from={from_date}&range.to={to_date}&size=50&number={page}"
                )
                try:
                    data = self._request("GET", f"{CERT_BASE}{path}")
                    body = data.get("result", {}).get("body", [])
                    if not body:
                        break
                    for o in body:
                        o["_market"] = m
                    all_body.extend(body)
                    if len(body) < 50:
                        break
                    page += 1
                except Exception:
                    break

        return {"result": {"body": all_body}}

    def pending_orders(self) -> dict:
        """미체결 주문."""
        return self._get("/api/v1/trading/orders/histories/all/pending")

    def orderable_amount(self) -> dict:
        """주문 가능 금액."""
        return self._get("/api/v1/dashboard/common/cached-orderable-amount")

    def exchange_rate(self) -> dict:
        """환율."""
        return self._get("/api/v1/exchange/usd/base-exchange-rate")

    # ── 종목 검색 & 시세 API ─────────────────

    def search_stock(self, query: str) -> list:
        """종목 검색. 티커/종목명/종목코드로 검색하여 토스 내부 코드를 반환한다.

        Returns:
            list of dict: [{stockCode, stockName, stockSymbol(?), companyCode, ...}, ...]
        """
        result = self._post("/api/v1/search/stocks", {"query": query}, base=INFO_BASE)
        return result.get("result", [])

    def resolve_toss_code(self, ticker: str) -> str | None:
        """티커/종목코드 → 토스 내부 코드 변환.

        규칙:
        - 한국 종목 (6자리 숫자): 'A' prefix 붙임 (예: '005930' → 'A005930')
        - 미국 종목 (영문 티커): search API로 EXACT 매치 검색

        Returns:
            str: 토스 내부 코드 (예: 'A005930', 'US19990122001')
            None: 검색 실패 시
        """
        # 한국 종목: 6자리 숫자 → A prefix
        if re.match(r"^\d{6}$", ticker):
            return f"A{ticker}"

        # 이미 A prefix 형태
        if re.match(r"^A\d{6}$", ticker):
            return ticker

        # 미국 종목: 검색 API
        items = self.search_stock(ticker)
        for item in items:
            if item.get("matchType") == "EXACT":
                return item.get("stockCode")
        # EXACT 없으면 첫 번째 결과
        if items:
            return items[0].get("stockCode")
        return None

    def stock_price(self, toss_code: str) -> dict:
        """토스 내부 코드로 시세 조회.

        Args:
            toss_code: 토스 내부 코드 (예: 'A005930', 'US19990122001')

        Returns:
            dict: {open, high, low, close, volume, base, changeType, currency,
                   closeKrw, marketCap, high52w, low52w, tradeDateTime, ...}
        """
        result = self._get(f"/api/v1/stock-prices/{toss_code}")
        return result.get("result", {})

    def stock_price_by_ticker(self, ticker: str) -> dict | None:
        """티커/종목코드로 시세 조회 (내부 코드 자동 변환).

        Args:
            ticker: 'NVDA', '005930', 'A005930' 등

        Returns:
            dict: stock_price() 결과 + '_toss_code' 키 추가
            None: 종목을 찾지 못한 경우
        """
        toss_code = self.resolve_toss_code(ticker)
        if not toss_code:
            return None
        price = self.stock_price(toss_code)
        price["_toss_code"] = toss_code
        return price

    def watchlist_prices(self, tickers: list[str]) -> list[dict]:
        """다종목 시세 일괄 조회.

        Args:
            tickers: ['NVDA', 'GOOGL', '005930', ...] 형태의 티커 목록

        Returns:
            list of dict: [{ticker, toss_code, name, close, base, change, change_pct,
                            high, low, volume, currency, close_krw, trade_datetime}, ...]
        """
        results = []
        for ticker in tickers:
            entry = {"ticker": ticker}
            try:
                # 코드 변환
                toss_code = self.resolve_toss_code(ticker)
                if not toss_code:
                    entry["error"] = "종목을 찾을 수 없음"
                    results.append(entry)
                    continue

                entry["toss_code"] = toss_code

                # 검색으로 종목명 가져오기
                search_items = self.search_stock(ticker)
                if search_items:
                    entry["name"] = search_items[0].get("stockName", ticker)
                else:
                    entry["name"] = ticker

                # 시세 조회
                price = self.stock_price(toss_code)
                close = price.get("close", 0)
                base = price.get("base", 0)
                change = close - base if close and base else 0
                change_pct = (change / base * 100) if base else 0

                entry.update({
                    "close": close,
                    "base": base,
                    "change": change,
                    "change_pct": change_pct,
                    "high": price.get("high", 0),
                    "low": price.get("low", 0),
                    "volume": price.get("volume", 0),
                    "currency": price.get("currency", ""),
                    "close_krw": price.get("closeKrw"),
                    "market_cap": price.get("marketCap"),
                    "trade_datetime": price.get("tradeDateTime", ""),
                })
            except Exception as e:
                entry["error"] = str(e)[:100]
            results.append(entry)
        return results

    # ── 매매 API ──────────────────────────────

    def _detect_market(self, symbol: str) -> str:
        """종목코드로 시장 판별. 6자리 숫자 or A+6자리 → 'kr', 그 외 → 'us'."""
        if re.match(r"^A?\d{6}$", symbol):
            return "kr"
        return "us"

    def _build_order_payload(self, symbol: str, side: str, qty: int,
                             price: int, with_order_key: bool = True) -> dict:
        """토스증권 주문 공통 페이로드 생성."""
        toss_code = self.resolve_toss_code(symbol)
        if not toss_code:
            raise ValueError(f"종목을 찾을 수 없습니다: {symbol}")

        market = self._detect_market(symbol)
        payload = {
            "stockCode": toss_code,
            "market": market,
            "currencyMode": "KRW",
            "tradeType": side.lower(),        # "buy" or "sell"
            "price": int(price),
            "quantity": int(qty),
            "orderAmount": int(price) * int(qty),
            "orderPriceType": "00",           # 00=지정가(limit)
            "agreedOver100Million": False,
            "marginTrading": False,
            "max": False,
            "isReservationOrder": False,
            "openPriceSinglePriceYn": False,
        }
        if with_order_key:
            payload["withOrderKey"] = True
        if market != "kr":
            payload["allowAutoExchange"] = True
        return payload

    def order_preview(self, symbol: str, side: str, qty: int, price: int) -> dict:
        """주문 미리보기 (prepare — 체결 없음, orderKey 반환)."""
        payload = self._build_order_payload(symbol, side, qty, price, with_order_key=True)
        return self._post("/api/v2/wts/trading/order/prepare", payload, base=CERT_BASE)

    def order_place(self, symbol: str, side: str, qty: int, price: int,
                    order_key: str = None, close: int = None) -> dict:
        """주문 실행 (create — ⚠️ 실제 체결).

        Args:
            order_key: order_preview()에서 받은 orderKey. 있으면 헤더에 추가.
            close: 현재가. extra 필드에 사용.
        """
        payload = self._build_order_payload(symbol, side, qty, price, with_order_key=False)
        # extra 필드 추가
        payload["extra"] = {
            "close": close or int(price),
            "orderMethod": "종목상세__주문하기",
        }
        # orderKey가 있으면 헤더에 추가
        if order_key:
            saved_headers = self._headers.copy()
            self._headers["X-Order-Key"] = order_key
            try:
                return self._post("/api/v2/wts/trading/order/create", payload, base=CERT_BASE)
            finally:
                self._headers = saved_headers
        return self._post("/api/v2/wts/trading/order/create", payload, base=CERT_BASE)

    def order_cancel(self, order_date: str, order_no: str, stock_code: str = None) -> dict:
        """주문 취소."""
        payload = {}
        if stock_code:
            toss_code = self.resolve_toss_code(stock_code)
            payload = {
                "stockCode": toss_code,
                "tradeType": "buy",
                "withOrderKey": True,
                "isReservationOrder": False,
            }
        return self._post(
            f"/api/v2/wts/trading/order/cancel/prepare/{order_date}/{order_no}",
            payload, base=CERT_BASE
        )

    def trading_status(self, symbol: str) -> dict:
        """종목 거래 상태 확인 (거래정지 여부 등)."""
        toss_code = self.resolve_toss_code(symbol)
        return self._get(f"/api/v3/trading/order/{toss_code}/trading-status", base=CERT_BASE)

    def orderable_quantity(self, symbol: str, side: str = "sell") -> dict:
        """주문 가능 수량 조회."""
        toss_code = self.resolve_toss_code(symbol)
        return self._get(
            f"/api/v1/trading/orders/calculate/{toss_code}/orderable-quantity/{side}?forceFetch=false",
            base=CERT_BASE
        )

    # ── 유틸리티 ──────────────────────────────

    def check_session(self) -> bool:
        """세션 유효성 확인."""
        try:
            self.accounts()
            return True
        except (SessionExpiredError, RuntimeError):
            return False


# ──────────────────────────────────────────────
# CLI — 단독 실행 시 간단한 테스트
# ──────────────────────────────────────────────

if __name__ == "__main__":
    try:
        client = TossClient()
        print("[OK] 세션 로드 성공")
        if client.check_session():
            print("[OK] 세션 유효 — API 연결 정상")
        else:
            print("[WARN] 세션이 만료되었을 수 있습니다")
    except SessionNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except SessionExpiredError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
