# 종목 분석

사용자가 제공한 종목 티커를 분석한다: $ARGUMENTS

## 실행 순서

1. 패키지 설치 (세션 첫 실행이면):
   ```
   pip install yfinance yt-dlp google-api-python-client beautifulsoup4 lxml --break-system-packages -q
   ```

2. 종목 데이터 수집:
   ```
   cd default/_scripts && python fetch_stock.py $ARGUMENTS
   ```
   - 한국 종목이면 `--market KR` 추가
   - 미국 종목이면 `--market US` 추가

3. 생성된 노트를 확인하고, 사용자에게 핵심 지표 요약을 보여주고 대화 시작

**중요: 투자 추천을 하지 않는다. 팩트와 데이터만 제공한다.**
