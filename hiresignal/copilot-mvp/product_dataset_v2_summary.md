# Product Dataset V2 Summary

- 기준 데이터: merged_results_88.jsonl
- 공개 JSON: product_dataset_v2_public.json
- 원본 자막/근거 문장/API 키는 공개 산출물에서 제외

## 전체
- 영상 수: 86

## 도메인 분포
- semiconductor: 30
- hyundai: 17
- finance: 17
- general_interview: 17
- retail_consumer: 5

## 상위 직무 과업
- [semiconductor] 이상 원인 분석: 20
- [semiconductor] 장비/현장 대응: 20
- [semiconductor] 수율/품질 개선: 19
- [general_interview] 경험 2개로 질문 유도: 16
- [finance] 고객 응대/상담: 13
- [hyundai] R&D/생산제조 협업: 12
- [finance] 경제/금융 필기 준비: 12
- [general_interview] 1분 자기소개 설계: 12
- [hyundai] 품질 검증/마지막 점검: 10
- [finance] 금융상품 설명/세일즈: 10
- [hyundai] 자기소개 PT: 9
- [hyundai] 파이로트/양산 전 평가: 8
- [general_interview] 자연형/전략형 답변: 8
- [finance] PT/BEI 면접 대응: 7
- [hyundai] 구매/협력사 조율: 6
- [semiconductor] 조건 최적화/DOE: 6

## 상위 평가 기준
- [semiconductor] 직무 이해도: 28
- [semiconductor] 데이터 기반 문제해결: 21
- [semiconductor] 현장 적응: 19
- [hyundai] 회사-직무 연결: 17
- [general_interview] 질문 유도: 17
- [semiconductor] 산업 이해: 16
- [finance] 은행 관심 증거: 16
- [finance] 사람 응대 경험: 15
- [general_interview] 구체적 경험: 15
- [finance] 고객 신뢰: 14
- [semiconductor] 협업/커뮤니케이션: 12
- [hyundai] 필살기 경험: 10
- [finance] 필기 루틴: 10
- [hyundai] 협업/조율: 9
- [finance] 과장 없는 답변: 8
- [general_interview] 외운 티 감소: 8

## 제품 기능 신호
- 경험 카드 데이터/수율 필드: 30
- 직무별 자소서 번역: 30
- 공정·설비·양산 면접 시뮬레이션: 30
- 자소서-PT 일관성 검사: 17
- 필살기 경험 2개 선별: 17
- 품질/구매/R&D 직무 번역: 17
- 은행 관심 증거 점검: 17
- PT/세일즈/BEI 면접 모드: 17
- 필기 루틴 관리: 17
- 1분 자기소개 경험 2개 설계: 17
- 자연형 답변 훈련: 17
- 꼬리질문 생성: 17
- 브랜드/고객 경험 번역: 5
- 계열사·직무 선택 점검: 5
- PT/발표 스토리라인 코칭: 5

## 이번 batch5 반영 포인트
- 회사별 큐레이션 21건을 추가해 전체 제품 백데이터가 86개 영상으로 확장됨
- 반도체/현대차/금융권 회사별 데이터가 두꺼워졌고, CJ·아모레·LG생활건강은 retail_consumer 도메인으로 별도 집계됨
- 소비재/유통은 브랜드/고객 경험 번역, 계열사·직무 선택, PT/발표 스토리라인 코칭 기능 후보로 연결됨
