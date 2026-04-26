---
name: investment-masters
description: |
  투자 대가들의 검증된 투자 원칙과 프레임워크를 활용하여 종목, 아이디어, 포트폴리오를 분석하고 판단하는 스킬.
  이 스킬은 사용자가 투자 아이디어를 평가하거나, 종목을 분석하거나, 매수/매도 판단을 고민하거나, 포트폴리오 리뷰를 요청할 때 사용한다.
  다음과 같은 상황에서 반드시 이 스킬을 활용한다:
  - "이 종목 어떻게 생각해?", "이거 살만해?", "이 아이디어 평가해줘"
  - "버핏이라면?", "멍거 관점에서", "대가들의 관점으로"
  - 종목 분석, 투자 아이디어 검토, 매수/매도 판단, 밸류에이션 논의
  - "리스크가 뭐야?", "약점이 뭐야?", "반대 논거", "스트레스 테스트"
  - 투자 심리, 시장 사이클, 포지션 사이징 관련 논의
  - "investment masters", "투자 대가", "투자 원칙", "프레임워크 분석"
  MANDATORY TRIGGERS: 종목 분석, 투자 판단, 아이디어 평가, 매수 매도, 밸류에이션, 투자 대가, 버핏, 멍거, 린치, 하워드 막스, 드러켄밀러, 그레이엄, 소로스, 피셔, 리루, 템플턴, 리버모어
---

# Investment Masters Framework — 투자 대가 분석 스킬

이 스킬은 26명의 투자 대가들의 원칙을 체계화하여, 사용자의 투자 아이디어와 종목 분석에 실전적으로 적용한다.

## 핵심 목적

사용자가 투자 판단을 내릴 때, 단순히 숫자를 나열하는 것이 아니라 **검증된 투자 철학의 렌즈**로 아이디어를 다각도로 평가한다. 각 대가의 관점은 서로 다른 측면을 비추므로, 여러 프레임워크를 교차 적용하여 블라인드 스팟을 최소화한다.

## 분석 프로세스

투자 아이디어나 종목을 평가할 때, 다음 순서로 진행한다:

### 1단계: 상황 파악 — 어떤 유형의 투자인가?

먼저 분석 대상의 성격을 파악하고, 가장 적합한 대가 프레임워크를 선택한다:

| 투자 유형 | 핵심 적용 대가 | 보조 적용 대가 |
|-----------|---------------|---------------|
| 가치주 (저평가 발굴) | Graham, Klarman, Templeton | Buffett, Munger, Neff |
| 성장주 (복리 성장) | Fisher, Lynch, Li Lu | Buffett, Munger |
| 턴어라운드/특수상황 | Greenblatt, Klarman, Icahn | Lynch, Ackman |
| 매크로/테마 투자 | Druckenmiller, Soros, Dalio | Tudor Jones, Rogers, Grantham |
| 트레이딩/타이밍 | Livermore, Tudor Jones, Druckenmiller | Soros, Gann |
| 역발상/컨트래리안 | Templeton, Marks, Grantham | Klarman, Munger |

### 2단계: 핵심 대가 프레임워크 적용

상황에 맞는 3~5명의 대가 프레임워크를 적용한다. 각 대가의 상세 원칙은 `references/` 디렉토리에서 참조한다:
- `references/value-investors.md` — Graham, Buffett, Munger, Klarman, Templeton, Neff, Li Lu, Greenblatt
- `references/growth-investors.md` — Fisher, Lynch
- `references/macro-traders.md` — Soros, Druckenmiller, Dalio, Tudor Jones, Rogers, Grantham
- `references/special-situations.md` — Icahn, Ackman, Livermore, Robertson, Gann

각 대가별로 다음을 수행한다:

**A) 해당 대가의 핵심 질문 던지기**
- 이 대가라면 이 투자에 대해 어떤 질문을 먼저 할 것인가?
- 해당 프레임워크에서 가장 중요한 판단 기준은 무엇인가?

**B) Pass/Fail 판정**
- 해당 대가의 핵심 원칙에 비추어, 이 투자가 통과하는가 실패하는가?
- 통과하지 못하는 원칙이 있다면, 그것이 deal-breaker인가 아닌가?

**C) 해당 대가만의 고유한 인사이트**
- 다른 프레임워크에서는 보이지 않는, 이 대가의 관점에서만 드러나는 포인트는?

### 3단계: 교차 검증 — 대가들이 동의하는가, 충돌하는가?

여러 대가의 판단을 종합한다:
- **합의 영역**: 대부분의 대가가 동의하는 강점/약점
- **충돌 영역**: 대가마다 다른 결론이 나오는 부분 (이것이 가장 중요한 논의 포인트)
- **블라인드 스팟**: 어떤 대가의 프레임워크로도 평가하기 어려운 영역

### 4단계: 실전 판단으로 귀결

추상적 분석에 머물지 않고 구체적 결론을 제시한다:
- **종합 평가**: 투자 매력도 (강한 매수 / 매수 / 중립 / 회피 / 강한 회피)
- **핵심 전제**: 이 투자가 성공하려면 반드시 맞아야 하는 가정 1~3개
- **킬 조건**: 이 중 하나라도 발생하면 즉시 재검토해야 하는 시나리오
- **포지션 사이징 시사점**: 확신 수준에 따른 적정 비중 (드러켄밀러식 접근)
- **진입 타이밍**: 지금이 적기인가, 기다려야 하는가 (리버모어/튜더 존스식 접근)

---

## 대가별 핵심 체크리스트 (Quick Reference)

이 섹션은 전체 분석 없이 빠르게 참조할 때 사용한다. 심층 분석 시에는 반드시 `references/` 파일을 읽는다.

### Warren Buffett — "10년 보유할 수 있는가?"
- **경쟁 우위(Moat)**: 이 회사의 경쟁 우위는 무엇이고, 지속 가능한가?
- **경영진**: 정직하고 유능한 경영진인가? 자본 배분을 잘 하는가?
- **이해 가능성**: 이 사업을 내가 충분히 이해하는가? (Circle of Competence)
- **가격 vs 가치**: "좋은 회사를 적정 가격에" — 현재 가격이 내재가치 대비 합리적인가?
- **장기 전망**: 10년 후에도 이 사업이 존재하고 성장하고 있을까?
- 핵심 격언: "Rule No.1: Never lose money. Rule No.2: Never forget Rule No.1."

### Charlie Munger — "바보도 운영할 수 있는 사업인가?"
- **인센티브 구조**: 경영진, 직원, 고객의 인센티브가 정렬되어 있는가?
- **역산 사고(Inversion)**: "이 투자가 실패하려면 무엇이 필요한가?" → 그 조건이 현실적인가?
- **기회비용**: 이것보다 더 나은 투자 대안이 있지 않은가?
- **정신 모델**: 다학제적 렌즈(심리학, 물리학, 생물학)로 볼 때 빠뜨린 관점은?
- **집중 투자**: 확신이 높으면 큰 베팅, 낮으면 패스 — 중간은 없다
- 핵심 격언: "Invert, always invert." / "The big money is in the waiting."

### Benjamin Graham — "안전마진이 충분한가?"
- **안전마진(Margin of Safety)**: 내재가치 대비 할인율이 충분한가? (최소 30%)
- **재무 건전성**: 부채비율, 유동비율, 20년 배당 이력 등 정량 기준 통과?
- **Mr. Market**: 시장의 감정에 휘둘리고 있지 않은가?
- **수비적 vs 공격적**: 사용자의 투자 역량에 맞는 접근인가?
- 핵심 격언: "In the short run, the market is a voting machine. In the long run, it is a weighing machine."

### Howard Marks — "2차적 사고로 남들과 다른 결론에 도달했는가?"
- **2차적 사고(Second-Level Thinking)**: 컨센서스와 같은 생각이면 초과수익 없다. 남들이 간과한 것은?
- **사이클 위치**: 지금 시장 사이클에서 어디에 있는가? (낙관의 정점? 비관의 바닥?)
- **가격이 전부**: 아무리 좋은 자산도 비싸게 사면 나쁜 투자. 아무리 나쁜 자산도 싸게 사면 좋은 투자.
- **리스크 vs 수익**: 높은 리스크가 높은 수익을 보장하지 않는다. 리스크의 본질을 이해하고 있는가?
- 핵심 격언: "The biggest investing errors come not from factors that are informational or analytical, but from those that are psychological."

### Peter Lynch — "이 회사의 스토리를 한 문장으로 설명할 수 있는가?"
- **회사 분류**: Fast Grower / Stalwart / Slow Grower / Cyclical / Turnaround / Asset Play?
- **PEG 비율**: PER ÷ 성장률 — 1 이하면 매력적, 2 이상이면 비싸다
- **일상의 투자**: 내가 소비자/업계인으로서 이 회사를 직접 관찰할 수 있는가?
- **과도한 분산 경계**: 잘 모르는 20개보다 잘 아는 5개가 낫다
- 핵심 격언: "Know what you own, and know why you own it."

### Stanley Druckenmiller — "비대칭 베팅인가?"
- **비대칭 수익구조**: 틀려도 적게 잃고, 맞으면 크게 버는 구조인가?
- **유동성 추종**: 중앙은행의 유동성 방향이 이 투자에 우호적인가?
- **집중 베팅**: 확신이 있으면 올인에 가깝게, 확신이 없으면 아예 하지 마라
- **미래에 투자**: 현재가 아닌 12~18개월 후의 세상에 베팅하고 있는가?
- **손실 회피**: 50% 손실은 100% 수익이 필요하다. 큰 손실을 절대 내지 마라
- 핵심 격언: "It's not whether you're right or wrong, it's how much money you make when you're right."

### George Soros — "시장의 반사성을 이용할 수 있는가?"
- **반사성(Reflexivity)**: 시장 참여자의 인식이 펀더멘탈을 변화시키는 피드백 루프가 있는가?
- **결함 찾기**: 현재 지배적 내러티브의 약점은 어디인가?
- **생존 우선**: 먼저 살아남고, 그다음에 수익을 추구한다
- **가설 검증**: 소규모 포지션으로 가설을 테스트하고, 맞으면 확대한다
- 핵심 격언: "Money is made by discounting the obvious and betting on the unexpected."

### Philip Fisher — "성장의 질이 높은가?"
- **Scuttlebutt 방법**: 고객, 경쟁사, 공급업체로부터 회사의 실체를 직접 확인했는가?
- **15개 체크포인트**: 매출 성장성, 이익률, R&D, 영업조직, 경영진 깊이 등
- **성장의 질**: 매출 성장이 진짜 유기적 성장인가, 인수·일회성인가?
- **매도 기준**: 비즈니스 퀄리티가 바뀌지 않으면 팔지 않는다. 가격만으로 팔지 않는다
- 핵심 격언: "Don't quibble over eighths." (좋은 주식이면 약간의 가격 차이에 집착하지 마라)

### Seth Klarman — "가치 함정은 아닌가?"
- **안전마진**: Graham을 계승하되 더 실전적 — 카탈리스트(촉매)가 있는가?
- **가치 함정 구별**: 싸다고 다 가치주가 아니다. 왜 싼지를 파악해야 한다
- **바텀업 분석**: 매크로 전망이 아닌 개별 기업의 본질적 가치에 집중
- **인내심**: 적절한 기회가 없으면 현금을 들고 기다린다
- 핵심 격언: "The stock market is the story of cycles and of the human behavior that is responsible for overreactions in both directions."

### Ray Dalio — "경제 기계를 이해하고 있는가?"
- **올웨더 사고**: 한 가지 시나리오에 올인하지 마라. 다양한 환경에서 생존하는 포트폴리오인가?
- **기대값 계산**: 확률 × 보상 — 감정이 아닌 시스템으로 판단
- **부채 사이클**: 현재 부채 사이클의 어디에 있는가? (디레버리징? 확장?)
- **원칙 기반**: 반복 가능한 의사결정 프로세스가 있는가?
- 핵심 격언: "He who lives by the crystal ball will eat shattered glass."

### John Templeton — "최대 비관론의 시점인가?"
- **최대 비관론**: "Bull markets are born on pessimism" — 지금 남들이 공포에 빠져 있는가?
- **글로벌 시야**: 한 나라에 갇히지 마라. 전 세계에서 가장 싼 시장은 어디인가?
- **재무 건전성**: 불황을 버틸 수 있는 기업만 매수한다
- 핵심 격언: "The four most dangerous words in investing are: 'This time it is different.'"

### Jeremy Grantham — "평균 회귀를 무시하고 있지 않은가?"
- **평균 회귀(Mean Reversion)**: 현재 밸류에이션/마진/수익률이 역사적 평균에서 얼마나 벗어나 있는가?
- **버블 식별**: 역사적 평균에서 2σ 이상 이탈하면 버블일 가능성
- **7년 예측**: 현재 밸류에이션으로 향후 7년 기대수익률은?
- 핵심 격언: "Profit margins are the most mean-reverting series in finance."

### Jesse Livermore — "타이밍이 맞는가?"
- **추세 확인**: 큰 흐름을 먼저 확인하고, 그 방향으로만 거래
- **물타기 금지**: 지고 있는 포지션에 추가하지 마라
- **인내**: "큰돈은 생각이 아니라 앉아 있는 것에서 나왔다"
- **시장 리더 추종**: 선도 업종의 선도주를 매매한다
- 핵심 격언: "Markets are never wrong — opinions often are."

### Paul Tudor Jones — "방어가 되어 있는가?"
- **방어 우선**: 수익보다 자본 보전이 먼저
- **5:1 보상비율**: 기대 보상이 리스크의 5배 이상인 거래만
- **가격이 진실**: 내 이론보다 시장 가격 움직임을 신뢰한다
- **감정 통제**: 매일 "내 포지션이 틀렸다면?"을 가정한다
- 핵심 격언: "The most important rule of trading is to play great defense, not great offense."

### Li Lu — "주인의 마음으로 보고 있는가?"
- **오너 마인드**: 이 회사 전체를 살 의향이 있는가?
- **지적 호기심**: 이 사업을 진정으로 깊이 이해하고 있는가?
- **집중 포트폴리오**: 확신 높은 소수에 집중
- **영구적 자본 손실**: 변동성이 아닌 영구적 자본 손실이 진짜 리스크
- 핵심 격언: "The best investors are the best learners."

---

## 대화에서의 적용 방식

이 스킬은 노트 작성용이 아니라 **실시간 대화에서 즉시 적용**하는 것이 핵심이다.

### 사용자가 종목/아이디어를 언급할 때
1. 해당 투자 유형에 맞는 대가 3~5명의 렌즈를 자동 적용
2. 사용자가 놓친 약점을 해당 대가의 관점에서 선제적으로 제시
3. 대가들 간 충돌 지점을 명시하여 논의를 유도

### 사용자가 확신을 표현할 때
1. 가장 강력한 반대 논거를 가진 대가의 프레임워크로 스트레스 테스트
2. "버핏이라면 이 부분을 물어볼 것이다", "소로스라면 반사성 리스크를 짚을 것이다" 등 구체적 인용
3. 사용자가 반론을 논파하면 → 확신 강화, 논파 못하면 → 재검토 유도

### 시장 상황을 논의할 때
1. Marks의 사이클 위치 판단, Grantham의 평균회귀, Dalio의 부채사이클 적용
2. Templeton의 비관/낙관 지표로 현재 심리 상태 진단
3. Druckenmiller의 유동성 방향 확인

---

## 참고: 상세 원칙 파일

심층 분석이 필요할 때 아래 파일을 참조한다:
- `references/value-investors.md` — 가치투자 대가 8명의 상세 원칙 (총 ~420개)
- `references/growth-investors.md` — 성장투자 대가 2명의 상세 원칙 (총 ~124개)
- `references/macro-traders.md` — 매크로/트레이딩 대가 6명의 상세 원칙 (총 ~296개)
- `references/special-situations.md` — 특수상황/행동주의 대가 4명의 상세 원칙 (총 ~195개)

출처: [KeepRule Investment Masters](https://keeprule.com/en/masters) — 26명 투자 대가, 총 1,300+ 투자 원칙
