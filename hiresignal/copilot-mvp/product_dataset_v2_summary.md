# Product Dataset V2 Summary

- 기준 데이터: core_results_hynix_h1.jsonl
- 원본 core 기준: 금융권, 현대차/기아, SK하이닉스, 삼성전자/반도체
- H1 추가: SK하이닉스 직무 세분화 후보 12건 중 processed 11건 반영
- 공개 JSON: product_dataset_v2_public.json
- 원본 자막/근거 문장/API 키는 공개 산출물에서 제외

## 전체
- core 영상 수: 75

## 도메인 분포
- semiconductor: 41
- hyundai: 17
- finance: 17

## 상위 직무 과업
- [semiconductor] 이상 원인 분석: 27
- [semiconductor] 장비/현장 대응: 27
- [semiconductor] 수율/품질 개선: 26
- [finance] 고객 응대/상담: 13
- [hyundai] R&D/생산제조 협업: 12
- [finance] 경제/금융 필기 준비: 12
- [hyundai] 품질 검증/마지막 점검: 10
- [finance] 금융상품 설명/세일즈: 10
- [hyundai] 자기소개 PT: 9
- [semiconductor] 조건 최적화/DOE: 9
- [hyundai] 파이로트/양산 전 평가: 8
- [finance] PT/BEI 면접 대응: 7
- [hyundai] 구매/협력사 조율: 6
- [hyundai] SDV/전장/인포테인먼트: 5

## 상위 평가 기준
- [semiconductor] 직무 이해도: 39
- [semiconductor] 데이터 기반 문제해결: 29
- [semiconductor] 현장 적응: 26
- [semiconductor] 산업 이해: 23
- [semiconductor] 협업/커뮤니케이션: 20
- [hyundai] 회사-직무 연결: 17
- [finance] 은행 관심 증거: 16
- [finance] 사람 응대 경험: 15
- [finance] 고객 신뢰: 14
- [hyundai] 필살기 경험: 10
- [finance] 필기 루틴: 10
- [hyundai] 협업/조율: 9
- [finance] 과장 없는 답변: 8
- [hyundai] 가치관/임원면접: 4

## 제품 기능 신호
- 경험 카드 데이터/수율 필드: 41
- 직무별 자소서 번역: 41
- 공정·설비·양산 면접 시뮬레이션: 41
- 자소서-PT 일관성 검사: 17
- 필살기 경험 2개 선별: 17
- 품질/구매/R&D 직무 번역: 17
- 은행 관심 증거 점검: 17
- PT/세일즈/BEI 면접 모드: 17
- 필기 루틴 관리: 17

## H1 반영 포인트
- SK하이닉스 공식 직무 영상 중심으로 양산기술, R&D공정, P&T, 소자, 설계, Maintenance 신호가 추가됨
- 아직 추출 결과의 role 라벨은 `반도체 직무`로 뭉치는 경향이 있어, 다음 단계는 role 정규화가 필요함
