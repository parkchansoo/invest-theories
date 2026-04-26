# 주식 데이터 수집 도구

Yahoo Finance, YouTube, DART, SEC EDGAR 등 다양한 외부 소스에서 데이터를 수집하여 옵시디언 노트로 자동 생성하는 스크립트 모음입니다. Cowork(Claude)를 통해 실행하거나 터미널에서 직접 실행할 수 있습니다.

## 필수 설치

```bash
pip install yfinance yt-dlp google-api-python-client dart-fss beautifulsoup4 lxml requests
```

## 노트 작성 방침

- 모든 노트는 **한글**로 작성 (번역이 어색한 전문용어는 영어 그대로 유지)
- 요약은 상단 5줄로만 간결하게, 그 아래에는 **원문 전문**을 최대한 보존
- 단락별로 가독성 좋게 구분하여 세부 내용을 직접 탐색할 수 있도록 구성

---

## 스크립트 목록

### 1. fetch_stock.py — 종목 분석 노트 생성
Yahoo Finance에서 종목의 기본 정보, 재무 지표, 밸류에이션, 애널리스트 의견을 자동 수집하여 옵시디언 노트로 생성합니다.

```bash
# 미국 주식
python fetch_stock.py AAPL --market US

# 한국 주식 (Yahoo Finance 티커: 종목코드.KS 또는 .KQ)
python fetch_stock.py 005930.KS --market KR

# 출력 디렉토리 지정
python fetch_stock.py NVDA --market US --output-dir ../01-Watchlist/US/

# JSON도 함께 저장
python fetch_stock.py TSLA --market US --json
```

### 2. fetch_earnings.py — 실적 데이터 수집
분기별 실적, EPS 서프라이즈 히스토리를 수집합니다.

```bash
python fetch_earnings.py AAPL
python fetch_earnings.py NVDA --output-dir ../05-Data-Inbox/Earnings/
```

### 3. compare_stocks.py — 종목 비교
여러 종목의 핵심 지표를 비교 테이블로 생성합니다.

```bash
python compare_stocks.py AAPL MSFT GOOGL NVDA
python compare_stocks.py 005930.KS 000660.KS --title "한국 반도체"
```

### 4. fetch_youtube.py — 유튜브 영상 스크립트 수집 ⭐
yt-dlp로 자막(수동/자동) 전문을 추출하고, YouTube Data API v3으로 상세 메타데이터를 조회합니다. 자막 원문 전체가 노트에 저장됩니다.

```bash
# 기본 사용 (한국어 자막 우선)
python fetch_youtube.py "https://www.youtube.com/watch?v=xxxxx"

# 영어 자막
python fetch_youtube.py "https://youtu.be/xxxxx" --lang en

# YouTube API 키로 상세 메타데이터 포함
python fetch_youtube.py "https://www.youtube.com/watch?v=xxxxx" --api-key AIza...

# 출력 디렉토리 지정
python fetch_youtube.py "URL" --output-dir ../05-Data-Inbox/Social/
```

**API 키 설정 (선택사항):**
YouTube Data API v3 키가 있으면 댓글 수 등 추가 메타데이터를 가져옵니다.
없어도 yt-dlp만으로 영상 정보 + 자막 추출이 가능합니다.

```bash
export YOUTUBE_API_KEY="AIzaSy..."
```

GCP 콘솔 → APIs & Services → YouTube Data API v3 활성화 후 API 키 발급

### 5. fetch_dart.py — DART 공시 원문 수집 (한국)
DART 전자공시시스템에서 공시 원문을 검색하고 전문을 텍스트로 추출합니다.

```bash
# 기업명으로 검색
python fetch_dart.py 삼성전자 --api-key "YOUR_DART_KEY"

# 종목코드로 검색
python fetch_dart.py 005930 --type 사업보고서 --limit 3

# 분기보고서만
python fetch_dart.py SK하이닉스 --type 분기보고서
```

**DART API 키 (필수):**
https://opendart.fss.or.kr 에서 회원가입 후 인증키 신청 (무료)

```bash
export DART_API_KEY="your_key_here"
```

공시 유형: 사업보고서, 반기보고서, 분기보고서, 주요사항보고 등

### 6. fetch_sec.py — SEC EDGAR 공시 원문 수집 (미국)
SEC EDGAR에서 미국 기업 공시를 검색하고 원문을 텍스트로 추출합니다. API 키 불필요.

```bash
# 최근 공시 전체
python fetch_sec.py AAPL

# 연간 보고서 (10-K)
python fetch_sec.py NVDA --type 10-K --limit 3

# 분기 보고서 (10-Q)
python fetch_sec.py TSLA --type 10-Q

# 수시 공시 (8-K)
python fetch_sec.py MSFT --type 8-K

# 원문 생략하고 목록만
python fetch_sec.py GOOGL --type 10-K --no-text
```

주요 공시 유형: 10-K (연간), 10-Q (분기), 8-K (수시), S-1 (IPO), DEF 14A (위임장)

---

## 한국 주식 티커 참고

Yahoo Finance에서 한국 주식은 다음 형식을 사용합니다:
- KOSPI: `{종목코드}.KS` (예: 005930.KS = 삼성전자)
- KOSDAQ: `{종목코드}.KQ` (예: 247540.KQ = 에코프로비엠)

## 환경변수 정리

```bash
# YouTube Data API v3 (선택 — 없어도 자막 추출 가능)
export YOUTUBE_API_KEY="AIzaSy..."

# DART Open API (한국 공시 수집 시 필수)
export DART_API_KEY="your_key_here"

# SEC User-Agent (선택 — 기본값 사용 가능)
export SEC_USER_AGENT="YourName research@email.com"
```

## Cowork에서 사용하기

Claude에게 자연어로 요청하면 됩니다:
- "NVDA 종목분석 노트 만들어줘"
- "삼성전자 최근 실적 정리해줘"
- "반도체 대장주들 비교해줘 (NVDA, AMD, INTC, AVGO)"
- "이 유튜브 영상 스크립트 가져와줘: https://youtube.com/watch?v=..."
- "NVDA 10-K 공시 가져와서 정리해줘"
- "삼성전자 최근 사업보고서 가져와줘"
