# 유튜브 영상 수집 및 정리

사용자가 제공한 유튜브 URL을 처리한다: $ARGUMENTS

## 실행 순서

1. 패키지 설치 (세션 첫 실행이면):
   ```
   pip install yfinance yt-dlp google-api-python-client beautifulsoup4 lxml --break-system-packages -q
   ```

2. 유튜브 자막 및 메타데이터 수집:
   ```
   cd default/_scripts && python fetch_youtube.py "$ARGUMENTS"
   ```

3. 출력된 파일을 `default/05-Data-Inbox/`의 적절한 주제 폴더로 이동
   - 파일명 형식: `{YYYY-MM-DD}-youtube-{제목}.md`
   - 주제 폴더 예: `AI-반도체/`, `매크로-금리/`, `우주-방산/` 등
   - 해당 폴더가 없으면 새로 생성

4. 노트를 열어서 아래 구조로 작성:
   - `## 요약 (5줄)` — 핵심 내용 5줄 이내
   - `## 상세 정리` — 원문 디테일에 가깝게 단락별 분리한 상세 정리글. 주요 논점, 인물, 숫자, 맥락을 빠짐없이 포함. **디테일 있게 작성할 것.**
   - `## 원문` — 기존 자막 전문 유지

5. 맵 갱신:
   ```
   cd default/_scripts && python build_map.py
   ```

6. 사용자에게 요약을 보여주고 대화 시작

**중요: 웹검색(WebSearch)을 하지 않는다. 확인 질문을 하지 않는다. 바로 실행한다.**
