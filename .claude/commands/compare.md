# 종목 비교 분석

사용자가 제공한 종목들을 비교 분석한다: $ARGUMENTS

## 실행 순서

1. 패키지 설치 (세션 첫 실행이면):
   ```
   pip install yfinance --break-system-packages -q
   ```

2. 비교 테이블 생성:
   ```
   cd default/_scripts && python compare_stocks.py $ARGUMENTS
   ```

3. 생성된 비교 노트를 확인하고 사용자에게 핵심 비교 포인트를 요약
