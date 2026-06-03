# Product Dataset Schema V2

생성: 2026-06-03

목적: 기존 `company`, `role`, `tech_trends` 중심 추출을 코파일럿 제품이 바로 쓸 수 있는 구조로 바꾼다.

입력:

- `core_results_finance_hyundai_semiconductor.jsonl`
- `transcript_cache.json`

외부 API:

- 사용하지 않음
- 이미 수집된 자막 캐시만 재가공

## 왜 바꾸는가

기존 스키마는 "삼성전자 / 공정기술 / HBM"처럼 키워드는 잘 뽑지만, 코파일럿이 실제로 무엇을 물어보고 어떻게 첨삭해야 하는지까지는 알려주지 못한다.

V2 스키마는 영상별로 아래를 뽑는다.

- 영상이 주장하는 준비 방향
- 직무가 실제로 하는 일
- 평가자가 보는 기준
- 자소서에서 확인할 체크리스트
- 면접 질문 후보
- 지원자 경험을 직무 언어로 바꾸는 규칙
- 제품 기능으로 연결되는 신호

## 필드 정의

### video_id

YouTube video id.

### url

YouTube watch URL.

### title_or_note

`urls.txt` 또는 배치 URL 파일에 적은 사람이 읽기 쉬운 영상 설명.

### company

기존 로컬 추출기가 판정한 회사명. 완벽하지 않으므로 제품 판단의 주 키로 쓰기보다는 참고값으로 본다.

### role

기존 로컬 추출기가 판정한 직무명. 일부 오분류가 있으므로 `job_tasks`, `evaluation_criteria`가 더 중요하다.

### domain

제품 도메인.

현재 제품 주입 대상:

- `semiconductor`
- `finance`
- `hyundai`

별도 archive 대상:

- `retail_consumer`
- `general_interview`

### keep

기존 수집 파이프라인에서 분석 대상으로 채택했는지 여부.

### video_claims

영상에서 반복적으로 드러난 핵심 주장. 로컬 전체 JSON에는 짧은 근거 스니펫이 들어가지만, 공개용 JSON에서는 제거한다.

### job_tasks

영상에서 언급된 직무 과업.

예:

- 반도체: 이상 원인 분석, 수율/품질 개선, 조건 최적화, 장비/현장 대응
- 금융권: 고객 응대, 금융상품 세일즈, PT/BEI 대응, 필기 준비
- 현대차: 품질 검증, 구매/협력사 조율, 파이로트/양산 전 평가, 자기소개 PT
- archive 소비재/유통: 브랜드/상품 기획, 고객/시장 이해, 유통/물류/커머스 운영, PT/발표/설득

### evaluation_criteria

영상에서 읽히는 평가 기준.

예:

- 데이터 기반 문제해결
- 직무 이해도
- 고객 신뢰
- 은행 관심 증거
- 회사-직무 연결
- 필살기 경험
- 회사/브랜드 이해
- 고객 관점

### resume_checks

자소서 첨삭 시 확인할 체크리스트.

예:

- 경험에 데이터, 원인 분석, 개선 행동, 결과가 있는가
- 은행 관심 증거가 행동으로 제시됐는가
- 자소서와 PT 내용이 일관되는가

### interview_questions

자막에서 명시적으로 잡힌 면접 질문 후보. 현재는 로컬 패턴 기반이라 품질이 균일하지 않다. 향후 LLM 추출로 개선할 대상이다.

### experience_translation_rules

지원자 경험을 직무 언어로 바꾸는 규칙.

예:

- 프로젝트 경험을 문제 상황 -> 데이터 확인 -> 원인 가설 -> 조건 최적화 -> 수율/품질 결과로 재작성
- 알바/인턴 경험을 고객 니즈 파악, 설명, 신뢰 회복, 민원 해결로 재작성
- 자소서 필살기 경험을 PT 슬라이드의 한 문장 메시지, 문제, 행동, 결과로 시각화

### product_features

해당 영상이 시사하는 제품 기능.

예:

- 경험 카드 데이터/수율 필드
- PT/세일즈/BEI 면접 모드
- 자소서-PT 일관성 검사
- 1분 자기소개 경험 2개 설계

### confidence

로컬 규칙으로 얼마나 충분한 신호가 잡혔는지.

- `high`
- `medium`
- `low`

## 현재 결과 요약

`product_dataset_v2.md` 기준:

- 영상 수: 53
- semiconductor: 24
- finance: 10
- hyundai: 10
- general_interview: 9

제품 기능 신호:

- 반도체: 경험 카드 데이터/수율 필드, 직무별 자소서 번역, 공정·설비·양산 면접 시뮬레이션
- 금융권: 은행 관심 증거 점검, PT/세일즈/BEI 면접 모드, 필기 루틴 관리
- 현대차: 자소서-PT 일관성 검사, 필살기 경험 2개 선별, 품질/구매/R&D 직무 번역
- 일반 면접: 1분 자기소개 경험 2개 설계, 자연형 답변 훈련, 꼬리질문 생성

## 한계

- 로컬 규칙 기반이므로 문맥 이해가 제한적이다.
- 기존 `company/role` 라벨은 일부 오분류가 있다.
- `interview_questions`는 패턴 기반이라 실제 면접 질문과 일반 설명이 섞일 수 있다.
- 공개용 JSON에서는 저작권 리스크를 줄이기 위해 자막 스니펫을 제거한다.

## 다음 개선

1. `company/role`보다 `domain/job_tasks/evaluation_criteria` 중심으로 제품 로직을 짠다.
2. LLM 추출을 쓴다면 `video_claims`, `job_tasks`, `evaluation_criteria`, `experience_translation_rules`를 우선 뽑는다.
3. 제품 UI에서는 지원자에게 회사/직무/목적을 먼저 묻고, 그에 맞는 경험 카드 필드를 다르게 보여준다.
