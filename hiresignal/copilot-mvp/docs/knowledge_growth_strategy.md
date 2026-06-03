# Knowledge Growth Strategy

생성: 2026-06-03

## 목적

회사별 취업 코파일럿의 백데이터를 어떤 순서로 확장할지 정의한다.

전제:

- 지금은 RAG를 구성하지 않는다.
- 먼저 정적 회사별 KB와 구조화 JSON을 기반으로 MVP를 만든다.
- 이후 합격 자소서, 면접 후기, 최신 채용공고/JD, 공식자료, 유튜브를 같은 구조의 evidence pack으로 추가한다.

## 현재 전략 판단

현재 방향은 맞다.

지금까지의 데이터는 단순 수집물이 아니라 회사별 코파일럿의 뼈대가 됐다.

- SK하이닉스: 메모리/직무 세분화, HBM4, Utility, PE, 품질보증
- 삼성전자 DS: 메모리 + S.LSI + Foundry + Package + Fab Automation
- 현대차/기아: 차량 개발, 생산기술, 품질, 구매, SDV, PT면접
- 금융권: 은행권 공통 + 은행별 skeleton

이제 무작정 데이터를 더 쌓기보다, 각 데이터가 코파일럿 기능으로 어떻게 쓰이는지 기준을 세워야 한다.

## 데이터 계층

### Layer 1. Company KB

역할:

- 회사별 기본 지식
- 직무 taxonomy
- 경험 번역 규칙
- 면접/자소서 체크리스트
- 산업 동향 연결 규칙

예:

- `companies/sk-hynix/copilot_kb.json`
- `companies/samsung-electronics/copilot_kb.json`

이 계층은 코파일럿의 기준이다.

### Layer 2. Official/JD Evidence

역할:

- 최신 채용공고
- 공식 직무기술서
- 공식 직무소개
- 회사 뉴스룸/기술 자료

활용:

- 직무 정의 확정
- 최신 채용 트랙 확인
- 지원동기 소재 검증
- 회사별 금지/주의 규칙 업데이트

우선순위:

1. 최신 채용공고/JD
2. 공식 직무소개
3. 공식 뉴스룸/기술자료
4. 정책/산업 공식자료

### Layer 3. YouTube / Interview Signal

역할:

- 취준생이 실제로 헷갈리는 지점
- 현직자/합격자 표현
- 면접 유형/말투
- PT/BEI/세일즈 같은 전형 체감

활용:

- 면접 질문 생성
- 답변 말투 보강
- 자소서 체크리스트 현실화
- 데이터 gap 탐지

주의:

- 유튜브는 직무 기준이 아니라 표현/신호다.
- 공식자료와 충돌하면 공식자료를 우선한다.
- 조회수보다 직무 특정성을 우선한다.

### Layer 4. Accepted Cover Letters

역할:

- 합격 자소서의 문항 구조
- 직무별 경험 선택 방식
- 문장 밀도와 근거 제시 방식
- 면접까지 방어 가능한 경험 패턴

활용:

- 자소서 문항별 체크리스트
- 합격 답변 구조 템플릿
- 문항 유형별 샘플 구조
- 과장/추상 표현 경고

주의:

- 원문을 그대로 프롬프트에 넣지 않는다.
- 저작권/개인정보 리스크가 있으므로 요약된 구조와 태그만 제품에 사용한다.
- 합격 자소서가 항상 좋은 글은 아니므로 품질 평가가 필요하다.

### Layer 5. Interview Reviews

역할:

- 실제 면접 질문
- 면접 유형
- 꼬리질문 방식
- 직무별 압박 포인트
- 은행/현대차처럼 전형 방식 차이

활용:

- 예상 질문 세트
- 꼬리질문 생성
- 답변 방어력 테스트
- 은행별/회사별 면접 모드

주의:

- 후기는 기억 기반이라 부정확할 수 있다.
- 질문 원문보다 질문 의도와 평가 기준을 구조화한다.
- 연도/전형/직무를 반드시 붙인다.

### Layer 6. User Feedback

역할:

- 실제 사용자가 어디서 막히는지
- 어떤 추천을 채택하는지
- 어떤 직무/회사 자료가 부족한지

활용:

- 다음 수집 우선순위
- 코파일럿 질문지 개선
- 회사별 KB 갱신

이 계층이 나중에 가장 중요해진다.

## Evidence Pack 표준 구조

RAG 전 단계에서는 모든 추가 데이터를 아래 구조로 저장한다.

```json
{
  "evidence_id": "samsung-ds-2026-process-tech-jd-001",
  "company_id": "samsung-electronics",
  "company_name": "삼성전자 DS",
  "industry": "semiconductor",
  "source_type": "job_posting",
  "source_url": "https://...",
  "collected_at": "2026-06-03",
  "year": 2026,
  "season": "상반기",
  "role": "반도체공정기술",
  "track": "DS",
  "source_quality": "official",
  "usage_level": "high",
  "copyright_policy": "structure_only",
  "facts": [
    "공정 Parameter 제시와 Set-up",
    "산포와 수율 개선",
    "Big Data 기반 공정 분석"
  ],
  "evaluation_criteria": [
    "공정 조건과 제품 특성의 관계 이해",
    "데이터 기반 원인 분석",
    "양산성/수율 개선 관점"
  ],
  "resume_checks": [
    "공정 변수와 결과 지표를 연결했는가",
    "수율/산포/불량 중 하나 이상의 개선 경험이 있는가"
  ],
  "interview_questions": [
    {
      "question": "공정 산포가 커질 때 어떤 순서로 원인을 좁히겠는가",
      "intent": "공정 데이터 분석과 문제해결 절차 확인"
    }
  ],
  "experience_translation_rules": [
    "실험 경험을 공정 Parameter -> 산포/수율 영향 -> 관리 기준 개선으로 재작성"
  ],
  "tags": [
    "process",
    "yield",
    "data_analysis"
  ]
}
```

## 추가 데이터별 처리 전략

### 1. 최신 채용공고/JD

가장 먼저 쌓아야 한다.

이유:

- 공식성이 높다.
- 최신 채용 트랙과 직무명을 반영한다.
- 코파일럿이 틀린 직무 조언을 하지 않게 한다.

추출 필드:

- 회사
- 사업부/트랙
- 직무명
- 주요 업무
- 필요 역량
- 우대사항
- 채용 연도/시즌
- 문항/전형
- 코파일럿 체크리스트

제품 활용:

- 직무 추천
- 자소서 체크리스트
- 스펙 gap 진단
- 면접 질문 생성

### 2. 합격 자소서

두 번째로 쌓는다.

이유:

- 사용자가 가장 직접적으로 원하는 기능이 자소서 첨삭이다.
- 회사/직무별로 어떤 경험이 선택되는지 볼 수 있다.

추출 필드:

- 회사/직무/연도
- 문항
- 문항 유형
- 경험 유형
- STAR 구조
- 정량 근거
- 직무 연결 문장
- 회사 연결 문장
- 면접 방어 가능성
- 과장 위험

제품 활용:

- 문항별 답변 구조 추천
- 경험 선택 피드백
- 좋은 문장보다 좋은 근거 우선 판단
- 꼬리질문 생성

저장 원칙:

- 원문 전문은 내부 원본 저장소에만 보관하거나 저장하지 않는다.
- 제품 주입용에는 구조화 결과만 둔다.
- 개인정보, 학교명, 실명, 세부 프로젝트명은 제거한다.

### 3. 면접 후기

세 번째로 쌓는다.

이유:

- 코파일럿 차별화는 면접 꼬리질문과 방어력에서 나온다.
- 회사별 면접 유형이 다르다.

추출 필드:

- 회사/직무/연도
- 면접 단계
- 면접 유형
- 질문
- 질문 의도
- 꼬리질문 패턴
- 답변 평가 기준
- 답변 리스크
- 분위기/난이도

제품 활용:

- 회사별 면접 시뮬레이션
- 직무 질문 생성
- 자소서 기반 꼬리질문
- 은행권 PT/BEI/세일즈 모드
- 현대차 자기소개 PT 모드

### 4. 공식 뉴스/기술자료

계속 보강하되 우선순위는 JD보다 낮다.

이유:

- 지원동기와 산업 이해에 좋다.
- 하지만 그대로 쓰면 회사 뉴스 요약이 된다.

추출 필드:

- 기술/사업 키워드
- 회사 전략
- 관련 직무
- 지원자 경험과 연결 가능한 포인트
- 쓰면 안 되는 일반론

제품 활용:

- 지원동기 보강
- 산업 질문 대비
- 직무별 최신 맥락

## 회사별 확장 우선순위

### 1순위: SK하이닉스

이유:

- 현재 KB 품질이 가장 높다.
- 유튜브와 공식자료가 모두 있다.
- 직무 세분화가 잘 되어 있다.

다음 데이터:

- 최신 채용공고/JD
- Product Engineering, 품질보증, Utility기술 합격 자소서/면접 후기
- HBM/P&T/PKG 관련 공식자료

### 2순위: 삼성전자 DS

이유:

- 공식 직무자료가 풍부하다.
- SK하이닉스와 비교 가능하다.
- DS 내부 직무 폭이 넓어 코파일럿 차별화가 좋다.

다음 데이터:

- 최신 DS 채용공고
- 평가 및 분석, 반도체공정기술, 설비기술, 신호 및 시스템 설계 후기
- 사업부별 차이: 메모리, S.LSI, Foundry, TSP

### 3순위: 현대차/기아

이유:

- 자소서-PT-면접 연결 기능을 검증하기 좋다.
- 품질/구매/파이로트 개발 데이터 신호가 좋다.

다음 데이터:

- 최신 공고/JD
- 품질/구매/생산기술/PT면접 후기
- 차량 SW/SDV, 기아 PBV 보강

### 유지 skeleton: 금융권

이유:

- 회사별 채용 특색이 중요하지만 현재 주 타겟은 아니다.
- 은행별 구조를 열어두는 것만으로 충분하다.

다음 타겟이 될 때:

- IBK기업은행부터 깊게 보강
- 우리은행 기업금융, 하나은행 PT/BEI 추가
- KB/신한/NH농협 최신 공고

## RAG 전 단계 운영 방식

RAG 없이도 다음처럼 동작한다.

```text
회사별 copilot_kb.json
  + evidence_packs/*.json
  + product_dataset_v2_public.json
  + user profile
  -> context packet
  -> LLM prompt
```

검색이 아니라 필터링이다.

필터 기준:

- company_id
- role
- task
- source_type
- usage_level
- year
- tags

예:

```ts
function selectEvidence(input) {
  return evidencePacks
    .filter(e => e.company_id === input.companyId)
    .filter(e => !input.role || e.role === input.role)
    .filter(e => e.usage_level !== "low")
    .filter(e => matchesTask(e, input.task))
    .sort(byOfficialThenRecentThenQuality)
    .slice(0, 5);
}
```

## RAG로 넘어갈 조건

아래 조건이 되기 전까지는 RAG를 하지 않는다.

- evidence pack이 회사당 100개 이상
- 사용자가 자유 검색형 질문을 많이 함
- 정적 필터링으로 필요한 근거 선택이 어려워짐
- 최신 공고/후기가 너무 많아 수동 context packet 관리가 어려워짐

RAG 도입 시에도 원칙은 같다.

- 원문 검색보다 구조화 evidence pack 검색 우선
- 공식/JD/합격자소서/면접후기를 source_type으로 분리
- 검색 결과는 반드시 회사/직무/task 필터를 통과해야 함

## 품질 관리

모든 evidence pack은 다음 점수를 가진다.

```json
{
  "source_quality": "official | verified | community | youtube | unknown",
  "usage_level": "high | medium | low | archive",
  "freshness": "current | recent | old | unknown",
  "role_specificity": "high | medium | low",
  "risk": {
    "copyright": "low | medium | high",
    "privacy": "low | medium | high",
    "hallucination": "low | medium | high"
  }
}
```

사용 기준:

- `official + high`: 직무 기준으로 사용
- `youtube/community + medium`: 표현/면접 신호로 사용
- `low`: 제품 prompt에는 넣지 않고 수집 판단에만 사용
- `archive`: 공개/제품 사용 제외

## 최종 전략

1. 지금은 RAG를 만들지 않는다.
2. 회사별 KB를 정규화해서 Context Builder를 만든다.
3. 최신 JD와 합격 자소서/면접 후기는 evidence pack으로 추가한다.
4. 원문보다 구조화된 규칙과 체크리스트를 제품에 넣는다.
5. 회사별 코파일럿이 셀링 포인트이므로 모든 데이터는 company_id를 기준으로 관리한다.
6. 금융권처럼 지금 타겟이 아닌 영역도 회사별 skeleton은 유지한다.

다음 구현 우선순위:

1. `normalizeCompanyKb()`
2. `buildContextPacket()`
3. task별 prompt template
4. evidence pack schema
5. 사용자 경험 카드 저장 구조
