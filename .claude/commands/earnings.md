# 실적 데이터 수집

사용자가 제공한 종목의 분기 실적 데이터를 수집한다: $ARGUMENTS

## 실행 순서

1. 패키지 설치 (세션 첫 실행이면):
   ```
   pip install yfinance --break-system-packages -q
   ```

2. 실적 데이터 수집:
   ```
   cd default/_scripts && python fetch_earnings.py $ARGUMENTS
   ```

3. 생성된 실적 노트를 확인하고 사용자에게 요약 보여주기
