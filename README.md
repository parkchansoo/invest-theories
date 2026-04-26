# 투자 리서치 워크스페이스

Claude Code(Cowork)와 Obsidian을 결합한 개인 투자 분석 시스템.
소스 수집부터 정리, 분석, 아이디어 관리, 매매 복기까지 하나의 워크플로우로 처리한다.

---

## 시작하기

### Step 1. 폴더 복사

```bash
cp -R investment-template/ 내이름/
cd 내이름/
```

### Step 2. Cowork 첫 대화 — 이름 등록

Claude Code에서 이 폴더를 열고, 첫 메시지로:

```
내 이름: 홍길동
```

Claude가 알아서 모든 설정 파일에서 이름을 교체하고, 다음 단계를 안내해줍니다.

**투자 정체성**도 이때 같이 채울 수 있습니다:
- 직접 채우고 싶으면 → Claude가 질문하면서 같이 작성
- 나중에 채우고 싶으면 → Step 3에서 거래내역 먼저 넣기
- 거래내역을 넣으면 Claude가 패턴을 분석해서 "이런 스타일인 것 같은데, 맞아?" 하고 제안해줍니다

### Step 3. 거래내역 연결 (분석의 출발점)

**거래내역이 있어야 분석이 시작됩니다.** 본인 증권사에 맞는 방법을 선택하세요.

#### 방법 A: API / MCP 연동 (실시간)

키움증권, 한국투자증권, 토스증권은 API 연동이 세팅되어 있습니다.

**1) `.env` 파일 생성:**
```bash
cd default/_scripts
cp .env.example .env
```

**2) 본인 증권사 API 키만 채우기:**

| 증권사 | 필요한 것 | 발급 방법 |
|--------|-----------|-----------|
| **키움증권** | App Key, Secret Key, 계좌번호, MCP 토큰 | [키움 OpenAPI](https://openapi.kiwoom.com/) 가입 → API 신청 → [키움 MCP](https://kiwoommcp.cleavework.com/) 가입 |
| **한국투자증권** | App Key, App Secret, 계좌번호 | [KIS Developers](https://apiportal.koreainvestment.com/) 가입 → 앱 등록 |
| **토스증권** | tossctl CLI 설치 | `brew tap JungHoonGhae/tossinvest-cli && brew install tossctl` → `tossctl auth login` |

> 키움증권은 **IP 등록**이 필요합니다 (포털에서 본인 IP 등록).
> 키움증권은 **모의투자**도 가능합니다 (`.env`에서 `KIWOOM_IS_MOCK=true`).

#### 방법 B: 거래내역 PDF 넣기 (오프라인)

다른 증권사를 쓰거나, API 세팅이 번거로우면 이 방법을 추천합니다.

1. 증권사 앱/웹에서 **거래내역 PDF** 다운로드
2. `default/_trade-data/originals/` 폴더에 넣기
3. Claude에게 **"거래내역 넣었어"** 라고 말하기

지원 증권사: 키움, 토스, 신한, 미래에셋, 카카오페이, NH

> PDF가 없는 증권사도 CSV나 스크린샷으로 대화하면서 입력 가능합니다.

### Step 4. 대화 시작!

**첫 대화 예시:**
- "거래내역 넣었어, 분석해줘" → 포트폴리오 분석 시작
- "내 포지션 보여줘" → API 연동된 경우 실시간 조회
- "이 유튜브 봐줘: https://youtube.com/..." → 소스 수집 & 정리
- "NVDA" → 종목 분석 노트 생성
- "투자 아이디어 정리해줘" → 대화 내용을 아이디어 노트로

**투자 정체성을 아직 안 채웠다면:**
- "내 거래내역 보고 내 투자 스타일 분석해줘" → Claude가 패턴 분석 후 제안
- 마음에 들면 "그걸로 투자 정체성 채워줘" → CLAUDE.md 자동 업데이트

---

## 폴더 구조

```
내이름/
├── CLAUDE.md                ← AI 행동 지침 (투자 정체성 여기에)
├── README.md                ← 이 파일
├── .mcp.json                ← MCP 서버 설정 (키움)
└── default/                 ← Obsidian 볼트
    ├── 00-Dashboard/Home.md ← 투자 대시보드 (자동 갱신)
    ├── 01-Watchlist/        ← 관심종목 (KR/US)
    ├── 02-Research/         ← 리서치
    ├── 03-Ideas/            ← 투자 아이디어
    ├── 04-Trading-Journal/  ← 매매일지
    ├── 05-Data-Inbox/       ← 소스 원문 (유튜브, 뉴스 등)
    ├── 07-Maps/             ← 자동생성 맵 (키워드, 종목, 주제)
    ├── Templates/           ← 노트 템플릿 6종
    ├── _scripts/            ← 데이터 수집 스크립트
    │   └── .env.example     ← API 키 템플릿 (cp → .env)
    └── _trade-data/         ← 거래내역 (모든 증권사 통합)
        ├── originals/       ← PDF 여기에 드롭
        ├── output/          ← 파싱 결과
        ├── sessions/        ← 증권사 인증/세션 파일 (.gitignore됨)
        └── scripts/         ← 거래내역 파서
```

---

## 슬래시 커맨드

URL을 붙여넣거나 티커를 입력하면 자동으로 수집·정리가 실행됩니다. 슬래시 커맨드로도 사용 가능:

| 커맨드 | 용도 | 예시 |
|--------|------|------|
| `/youtube` | 유튜브 영상 수집·정리 | `/youtube https://youtube.com/watch?v=xxx` |
| `/stock` | 종목 분석 | `/stock NVDA` |
| `/earnings` | 실적 데이터 | `/earnings AAPL` |
| `/compare` | 종목 비교 | `/compare NVDA AMD INTC` |
| `/news` | 뉴스 기사 수집·정리 | `/news https://example.com/article` |
| `/idea` | 아이디어 노트 작성 | `/idea AI-헬스케어 투자 테마` |
| `/dart` | DART 공시 수집 | `/dart 삼성전자` |
| `/sec` | SEC 공시 수집 | `/sec NVDA --type 10-K` |
| `/map` | 맵 갱신 | `/map` |

---

## 요구사항

- Python 3.x
- `pip install yfinance yt-dlp google-api-python-client beautifulsoup4 lxml`
- API 키: `default/_scripts/.env`에 설정
- [Obsidian](https://obsidian.md/) (권장, 필수 아님)

---

## FAQ

**Q: Obsidian이 꼭 필요한가요?**
A: 없어도 Claude와 대화하며 분석은 가능합니다. 다만 Obsidian으로 `default/` 폴더를 열면 대시보드, 종목맵, 위키링크 등이 시각적으로 연결되어 훨씬 편합니다.

**Q: 여러 증권사를 동시에 쓸 수 있나요?**
A: 네. `.env`에 여러 증권사 키를 다 넣으면 됩니다. PDF도 여러 증권사 것을 한꺼번에 넣을 수 있습니다.

**Q: 모의투자로 시작할 수 있나요?**
A: 키움증권은 `KIWOOM_IS_MOCK=true`로 모의계좌 연동 가능합니다. 한투도 모의투자 서버를 지원합니다.

**Q: 내 데이터가 외부로 나가나요?**
A: `.env`와 세션 파일은 `.gitignore`에 포함되어 있어 git에 올라가지 않습니다. 거래내역은 로컬에서만 처리됩니다.
