# Company Copilot Data

회사별 취업 코파일럿 데이터는 회사 단위로 분리한다.

각 회사 폴더의 대표 파일은 다음 기준을 따른다.

- `README.md`: 회사별 데이터 현황과 진입점
- `copilot_kb.md`: 사람이 읽는 최종 지식 베이스
- `copilot_kb.json`: LLM/copilot 주입용 구조화 데이터
- `judgment.md`: 데이터 품질, 한계, 계속 수집 여부 판단
- `roles/`: 직무 taxonomy, 직무 매핑 기준
- `sources/`: 공식자료, 뉴스, 유튜브 근거
- `collections/`: 수집 배치별 후보, URL, 리뷰
- `raw/`: 원본 분석 결과와 내부 검증용 산출물
- `scripts/`: 해당 회사 전용 빌더/정리 스크립트

운영 원칙:

1. 코파일럿이 직접 쓰는 파일은 `copilot_kb.json`을 기준으로 한다.
2. 사람이 검토하는 대표 문서는 `copilot_kb.md`와 `judgment.md`로 제한한다.
3. 원천 근거는 `sources/`와 `collections/`에 보관하되, 최상위에는 노출하지 않는다.
4. 회사가 늘어나도 같은 구조를 반복해 비교 가능하게 유지한다.
