# SEC EDGAR 공시 수집

미국 기업의 SEC 공시를 수집한다: $ARGUMENTS

## 실행 순서

1. 패키지 설치 (세션 첫 실행이면):
   ```
   pip install beautifulsoup4 lxml --break-system-packages -q
   ```

2. SEC 공시 수집:
   ```
   cd default/_scripts && python fetch_sec.py $ARGUMENTS
   ```
   - 예: `python fetch_sec.py NVDA --type 10-K`

3. 생성된 노트를 확인하고 사용자에게 핵심 내용을 요약
