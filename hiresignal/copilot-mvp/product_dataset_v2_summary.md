# Product Dataset V2 Summary

스키마: `v2-local-rules-2026-06-03`
영상 수: 53

## Domain Distribution
- semiconductor: 22
- hyundai: 13
- finance: 12
- general_interview: 6

## Top Company Roles
- 금융권 / 은행/금융: 8
- 삼성전자 / 공정기술: 7
- 현대자동차 / 공정기술: 4
- 현대자동차 / 직무미상: 4
- SK하이닉스 / 공정기술: 3
- SK하이닉스 / 반도체 직무: 2
- SK하이닉스 / Maintenance: 2
- 삼성전자 / 반도체 직무: 2
- 현대자동차 / Maintenance: 2
- 현대자동차 / 상용차: 2
- SK하이닉스 / 직무미상: 1
- 삼성전자 / 직무미상: 1
- 현대자동차 / UI/UX: 1
- 미상 / 설비: 1
- 미상 / 공정기술: 1

## Top Job Tasks
- [semiconductor] 장비/현장 대응: 16
- [semiconductor] 이상 원인 분석: 15
- [semiconductor] 수율/품질 개선: 15
- [hyundai] R&D/생산제조 협업: 10
- [finance] 고객 응대/상담: 10
- [finance] 경제/금융 필기 준비: 10
- [hyundai] 자기소개 PT: 9
- [hyundai] 품질 검증/마지막 점검: 8
- [finance] 금융상품 설명/세일즈: 8
- [hyundai] 파이로트/양산 전 평가: 7
- [semiconductor] 조건 최적화/DOE: 6
- [general_interview] 1분 자기소개 설계: 6
- [general_interview] 경험 2개로 질문 유도: 6
- [hyundai] 구매/협력사 조율: 5
- [hyundai] SDV/전장/인포테인먼트: 5
- [finance] PT/BEI 면접 대응: 5
- [finance] 기업/중소기업 이해: 4
- [semiconductor] 표준화/재발 방지: 3
- [general_interview] 자연형/전략형 답변: 3
- [semiconductor] 공정 상태 모니터링: 2

## Top Evaluation Criteria
- [semiconductor] 직무 이해도: 20
- [semiconductor] 데이터 기반 문제해결: 17
- [semiconductor] 산업 이해: 13
- [hyundai] 회사-직무 연결: 13
- [semiconductor] 현장 적응: 12
- [finance] 사람 응대 경험: 11
- [finance] 은행 관심 증거: 11
- [semiconductor] 협업/커뮤니케이션: 10
- [hyundai] 필살기 경험: 10
- [finance] 고객 신뢰: 10
- [finance] 필기 루틴: 9
- [hyundai] 협업/조율: 8
- [finance] 과장 없는 답변: 7
- [general_interview] 구체적 경험: 6
- [general_interview] 질문 유도: 6
- [hyundai] 가치관/임원면접: 3
- [general_interview] 외운 티 감소: 3
- [hyundai] PT 구성력: 2

## Product Feature Signals
- 경험 카드 데이터/수율 필드: 22
- 직무별 자소서 번역: 22
- 공정·설비·양산 면접 시뮬레이션: 22
- 자소서-PT 일관성 검사: 13
- 필살기 경험 2개 선별: 13
- 품질/구매/R&D 직무 번역: 13
- 은행 관심 증거 점검: 12
- PT/세일즈/BEI 면접 모드: 12
- 필기 루틴 관리: 12
- 1분 자기소개 경험 2개 설계: 6
- 자연형 답변 훈련: 6
- 꼬리질문 생성: 6

## Representative Records

### semiconductor: SK하이닉스 면접 질문 총정리 (당몰기/HIINT)
- company/role: SK하이닉스 / 반도체 직무
- confidence: medium
- job_tasks: 이상 원인 분석
- evaluation_criteria: 산업 이해
- product_features: 경험 카드 데이터/수율 필드, 직무별 자소서 번역, 공정·설비·양산 면접 시뮬레이션

### finance: 금융권/은행 취업 합격 튜토리얼 (바뀐 인재상/채용전략)
- company/role: 금융권 / 은행/금융
- confidence: high
- job_tasks: 고객 응대/상담, 금융상품 설명/세일즈, 경제/금융 필기 준비
- evaluation_criteria: 고객 신뢰, 사람 응대 경험, 은행 관심 증거, 필기 루틴
- experience_translation_rules:
  - 알바/인턴/봉사 경험을 고객 니즈 파악, 설명, 신뢰 회복, 민원 해결로 재작성
- product_features: 은행 관심 증거 점검, PT/세일즈/BEI 면접 모드, 필기 루틴 관리

### hyundai: 현대차 면접기출/지원동기 (면접도사)
- company/role: 현대자동차 / 공정기술
- confidence: medium
- job_tasks: 품질 검증/마지막 점검, R&D/생산제조 협업
- evaluation_criteria: 필살기 경험, 회사-직무 연결
- experience_translation_rules:
  - 프로젝트 경험을 품질 검증, 사전 문제 발견, 양산 전 개선, 협업 부서 조율로 재작성
- product_features: 자소서-PT 일관성 검사, 필살기 경험 2개 선별, 품질/구매/R&D 직무 번역

### general_interview: 면접관이 끄덕이는 1분 자기소개
- company/role: 미상 / 직무미상
- confidence: high
- job_tasks: 1분 자기소개 설계, 경험 2개로 질문 유도, 자연형/전략형 답변
- evaluation_criteria: 구체적 경험, 질문 유도, 외운 티 감소
- experience_translation_rules:
  - 1분 자기소개에는 질문받고 싶은 경험 2개만 남기고 스펙 나열을 제거
- product_features: 1분 자기소개 경험 2개 설계, 자연형 답변 훈련, 꼬리질문 생성
