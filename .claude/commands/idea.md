# 투자 아이디어 정리

대화 내용을 바탕으로 투자 아이디어 노트를 작성한다: $ARGUMENTS

## 실행 순서

1. `default/Templates/` 에서 아이디어 템플릿 확인

2. 대화에서 논의된 내용을 바탕으로 아이디어 노트 작성
   - 저장 위치: `default/03-Ideas/Active/`
   - 파일명: `{YYYY-MM-DD}-{아이디어제목}.md`
   - YAML frontmatter 포함

3. 관련 소스 노트들을 wikilink로 연결

4. 맵 갱신:
   ```
   cd default/_scripts && python build_map.py
   ```

5. 사용자에게 작성된 아이디어 노트 내용을 보여주기

**중요: 사용자의 판단을 대신하지 않는다. 대화에서 나온 팩트와 분석만 정리한다.**
