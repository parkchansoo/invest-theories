# 뉴스/웹 기사 수집 및 정리

사용자가 제공한 뉴스 URL을 처리한다: $ARGUMENTS

## 실행 순서

1. URL에서 본문 수집 (WebFetch 도구 사용, WebSearch 아님!)

2. `default/05-Data-Inbox/`의 적절한 주제 폴더에 노트 저장
   - 파일명: `{YYYY-MM-DD}-news-{제목}.md`
   - YAML frontmatter 포함 (source_type, source_url, date, topic, tickers, tags)

3. 노트 구조:
   - `## 요약 (5줄)` — 핵심 내용 5줄 이내
   - `## 상세 정리` — 단락별 디테일 있는 정리. 주요 논점, 인물, 숫자, 맥락 빠짐없이.
   - `## 원문` — 기사 전문

4. 맵 갱신:
   ```
   cd default/_scripts && python build_map.py
   ```

5. 사용자에게 요약을 보여주고 대화 시작

**중요: WebSearch를 사용하지 않는다. 확인 질문을 하지 않는다.**
