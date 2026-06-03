# SK hynix Copilot Data

SK하이닉스 회사별 취업 코파일럿 데이터 폴더다.

## 대표 파일

- `copilot_kb.md`: 최종 사람이 읽는 지식 베이스
- `copilot_kb.json`: 코파일럿 주입용 구조화 데이터
- `judgment.md`: 현재 데이터가 코파일럿 배경 데이터로 적합한지에 대한 판단

## 폴더

- `roles/`: 직무 taxonomy와 sub role 매핑 기준
- `sources/`: 유튜브 후보와 외부 근거 정리
- `collections/h1_youtube/`: SK하이닉스 H1 수집 배치
- `collections/gap_roles_g1/`: 부족 직무 보강 후보 배치
- `raw/`: 내부 분석 원본과 중간 산출물
- `scripts/`: SK하이닉스 지식 베이스 생성 스크립트

## 현재 판단

SK하이닉스는 회사별 코파일럿의 기준 템플릿으로 쓰기 좋다.

이유:

- 공식 Job Roles로 직무 구조를 잡을 수 있다.
- 유튜브 데이터로 취준생 혼동 지점과 현직자 표현을 보강할 수 있다.
- HBM4, Advanced MR-MUF, iHBM, advanced packaging 같은 최신 맥락을 직무별로 연결할 수 있다.
- Product Engineering, Utility기술, 품질보증처럼 일반 반도체 취업 조언에서 놓치기 쉬운 직무를 분리할 수 있다.

다음 회사인 삼성전자도 이 구조를 그대로 복제하되, 삼성전자 DS 기준의 직무 체계와 사업/기술 맥락에 맞춰 다시 채워야 한다.
