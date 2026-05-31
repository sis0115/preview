# Plantgram2 Final Product Brief

작성일: 2026-05-30

이 폴더는 Plantgram2의 최종 기능 구조, 메뉴별 화면 설명, 디자인 방향, AI 기획 검토 지점을 한곳에 모은 산출물이다. 현재 `plantgram2` 앱 코드와 개발/기획 문서를 기준으로 작성했다.

## 기준으로 본 자료

- `AGENTS.md`
- `docs/codex_bootstrap.md`
- `docs/plantgram2-implementation-plan/00_development_rules.md`
- `docs/plantgram2-implementation-plan/01_firestore_schema.md`
- `docs/plantgram2-implementation-plan/02_file_map.md`
- `docs/plantgram2-implementation-plan/03_current_plantgram2_inventory.md`
- `docs/agent-work/planning/2026-05-29_to_be_implementation_inventory.md`
- `docs/agent-work/planning/2026-05-29_master_feature_backlog.md`
- `docs/agent-work/planning/2026-05-29_development_sequence.md`
- `docs/agent-work/planning/2026-05-30_ai_record_interface_design.md`
- `plantgram2/docs/light_maintenance_log.md`
- `plantgram2/docs/legacy_menu_migration_audit.md`
- `plantgram2/lib/presentation/home/home_tab.dart`
- `plantgram2/lib/presentation/myplant/my_plant_home.dart`
- `plantgram2/lib/presentation/dictionary/dictionary_home.dart`
- `plantgram2/lib/presentation/dictionary/dictionary_detail.dart`
- `plantgram2/lib/presentation/record/record_home.dart`
- `plantgram2/lib/presentation/account/account_page.dart`
- `plantgram2/lib/presentation/community/community_post_list.dart`
- `plantgram2/lib/presentation/community/community_post_detail.dart`

## 산출물 구성

- [menu_overview.md](./menu_overview.md): 전체 메뉴와 앱 구조 요약
- [my_plant.md](./my_plant.md): 내 식물 메뉴 상세
- [dictionary.md](./dictionary.md): 식물사전 메뉴 상세
- [records.md](./records.md): 기록 메뉴 상세
- [account_community.md](./account_community.md): 계정 및 식물별 커뮤니티 상세
- [ai_planning.md](./ai_planning.md): AI 기능을 어디에 넣을지에 대한 검토안
- [html/index.html](./html/index.html): 화면 스크린샷 느낌의 정적 HTML 디자인 산출물

## 현재 앱의 핵심 방향

Plantgram2는 Plantgram1의 핵심 기능 중 식물 관리에 직접 연결되는 흐름을 Firebase, GetX, Repository 구조로 재구성한 앱이다. 현재 제품의 중심은 쇼핑/클래스/중고거래/상담 같은 레거시 확장 메뉴가 아니라, 사용자가 가진 식물을 등록하고 돌봄 일정을 관리하며, 식물사전과 기록을 통해 반복 관리를 쉽게 하는 데 있다.

기본 탭은 다음 4개다.

1. 내 식물
2. 사전
3. 기록
4. 계정

식물별 커뮤니티는 독립 하단 탭이 아니라 식물사전 상세에서 진입하는 식물 맥락형 기능으로 정리되어 있다. 이 구조는 MVP 범위를 작게 유지하면서도, 같은 식물을 키우는 사용자끼리 경험을 공유할 수 있게 한다.

## 디자인 느낌 요약

- 흰색 기반의 가벼운 모바일 앱 톤
- 연한 그린/민트 계열을 주요 행동 색상으로 사용
- 식물 카드, 돌봄 일정 카드, 사전 추천 섹션처럼 정보를 짧은 블록으로 나누는 구성
- 홈은 관리 대상과 해야 할 일을 빠르게 보여주는 운영형 화면
- 사전은 검색과 추천 섹션 중심의 탐색형 화면
- 기록은 필터와 타임라인 중심의 회고형 화면
- 계정은 설정과 공개 범위를 다루는 실용형 화면

## AI 기획 검토의 기본 전제

AI는 새 탭을 만드는 방식보다 기존 기록 흐름 안에 넣는 것이 적합하다. 현재 기획 문서의 방향도 "자연어를 식물 돌봄 기록 초안으로 변환"하는 좁고 명확한 기능을 우선한다.

예: "몬스테라 물 줬고 잎이 조금 말랐어"를 입력하면 식물, 기록 유형, 메모, 날짜를 추출해 사용자가 확인 후 저장한다.
