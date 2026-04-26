# DART 공시 수집

한국 기업의 DART 공시를 수집한다: $ARGUMENTS

## 실행 순서

1. 패키지 설치 (세션 첫 실행이면):
   ```
   pip install beautifulsoup4 lxml --break-system-packages -q
   ```

2. DART 공시 수집:
   ```
   cd default/_scripts && python fetch_dart.py $ARGUMENTS
   ```
   - 예: `python fetch_dart.py 삼성전자 --type 사업보고서`

3. 생성된 노트를 확인하고 사용자에게 핵심 내용을 요약
