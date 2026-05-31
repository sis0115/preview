# Plantgram2 Source-Based Screen Analysis

작성일: 2026-06-01

이 문서는 기획 문서가 아니라 `plantgram2/lib` Flutter 소스를 직접 읽고 정리한 화면/기능 기준이다.

## 읽은 주요 소스

- `lib/main.dart`
- `lib/controller/auth_controller.dart`
- `lib/binding/init_bindings.dart`
- `lib/presentation/login/signin.dart`
- `lib/presentation/home/home_tab.dart`
- `lib/presentation/myplant/myplant_home.dart`
- `lib/presentation/myplant/myplant_list.dart`
- `lib/presentation/myplant/myplant_schedule.dart`
- `lib/presentation/myplant/myplant_diary.dart`
- `lib/presentation/myplant/myplant_detail_page.dart`
- `lib/presentation/myplant/widget/myplant_point_view.dart`
- `lib/presentation/myplant/widget/plant_record_action_sheet.dart`
- `lib/presentation/myplant/widget/weather_view.dart`
- `lib/presentation/myplant/widget/watering_plant_view.dart`
- `lib/presentation/myplant/widget/recent_plant_actions.dart`
- `lib/presentation/add_myplant/add_screen.dart`
- `lib/presentation/dictionary/dictionary_home.dart`
- `lib/presentation/dictionary/dictionary_detail.dart`
- `lib/presentation/record/record_home.dart`
- `lib/presentation/account/account_page.dart`
- `lib/presentation/community/community_post_list.dart`
- `lib/presentation/community/community_post_detail.dart`
- `lib/controller/myplant_controller.dart`
- `lib/controller/add_plant_controller.dart`
- `lib/controller/dictionary_controller.dart`
- `lib/controller/record_controller.dart`

## 앱 진입

- `main.dart`는 `GetMaterialApp`에 로딩 화면을 먼저 표시한다.
- Firebase 초기화 후 `AuthController`가 주입된다.
- `AuthController`는 Firebase auth state를 구독한다.
- 로그아웃 상태면 `Signin`, 로그인 상태면 `InitBinding` 후 `HomeTab`으로 이동한다.

## 로그인

실제 구현:

- 흰 배경
- `plantgram_logo.png`
- `Plantgram`
- `식물을 기록하고 관리해보세요`
- 카카오 노란색 버튼 `카카오로 시작하기`
- 로딩 중 버튼 비활성화 및 spinner
- 처음 로그인하면 `식집사` 이름으로 프로필 생성 안내

## 홈 탭

실제 구현:

- `SnakeNavigationBar.color`
- 탭 4개:
  - 내 식물
  - 사전
  - 기록
  - 계정
- 기록 탭을 누르면 `RecordController.loadTimeline()` 호출
- 선택 탭은 `HomeController`에 저장된다.

## 내 식물 홈

실제 구현:

- `NestedScrollView`
- 상단 `SliverAppBar`, 높이 210
- 가로 카드:
  - `WeatherView`
  - `WateringPlantView`
  - `MyPlantPointView`
- 내부 탭:
  - 내식물
  - 일정
  - 다이어리

### WeatherView

- OpenWeather 데이터 기반
- 날씨 조건별 gradient
- AnimatedTextKit으로 문구 3개 순환
- 온도, 습도, 위치, 날씨 아이콘 표시
- 실패/없음 값은 `-` fallback

### WateringPlantView

- 물주기가 필요한 식물이 있을 때만 표시
- `물주기가 필요한 식물이 N개 있어요`
- 원형 dotted button `일괄로 물주기`
- 누르면 `queryUpdateAllMyPlant()`

### MyPlantPointView

- `나의 식물`
- 등록 식물 개수
- `식물 등록하기` 버튼
- 누르면 식물 등록 bottom sheet

## 내 식물 목록

실제 구현:

- `MyPlantList`는 `controller.myPlantList`를 `Obx`로 구독한다.
- 목록은 `MyPlantListCard`
- 빈 상태 문구는 `식물이 없습니다. 화면 필요`
- 카드 표시:
  - 식물 이미지
  - 식물 애칭
  - `Lv.N`
  - 물주기 지남/남음/오늘
  - 물주기 버튼 또는 관리 종료 badge

## 식물 등록

실제 구현:

- `MyPlantPointView.addPlant()`
- Bottom sheet 높이 0.8
- 제목 `키우는 식물을 등록해 주세요`
- 식물종 선택 전에는 애칭 입력 영역 숨김
- 식물종 선택은 `AddMyPlantScreen`으로 이동
- 식물종 선택 후 애칭 입력 표시
- 대표 이미지 선택:
  - dotted preview box
  - 앨범
  - 카메라
  - 삭제
- 관리 기준:
  - 식물 생일
  - 마지막 물준 날
  - 물주기
  - 영양제
  - 분갈이
  - 햇빛 선호
  - 수분 선호
  - 최저 온도
  - 최고 온도
  - 화분
  - 메모
- 저장 버튼:
  - 조건 충족 시 파란색 `등록하기`
  - 저장 중 `등록 중...`

## 식물 검색/선택

실제 구현:

- `AddMyPlantScreen`
- AppBar 안에 검색 입력 `식물검색..`
- 검색어 없을 때 최근 검색어 표시
- 전체 삭제, 개별 삭제
- 검색 결과 없으면 `검색 결과가 없습니다.`
- 검색 결과를 선택하면:
  - 검색어 저장
  - `MyplantController.updateSelectedName()`
  - AddPlantController에 server plant 기준값 반영
  - 등록 bottom sheet로 복귀

## 내 식물 상세

실제 구현:

- 대표 이미지가 있는 `SliverAppBar`
- 스크롤 후 title에 `Lv.N 애칭`
- 더보기 메뉴:
  - 관리 종료
  - 관리 재시작
- 레벨 게이지
- 애칭
- 식물종명/ID
- 설명
- 메모
- 함께한 날짜
- 물주기 주기
- 햇빛/수분/온도/화분
- 분갈이/영양제 주기
- D-Day 카드:
  - 물주기
  - 분갈이
  - 영양제
  - 추가 알림 `+`
- 최근 기록
- 하단 고정 버튼:
  - 살아있는 식물: `기록하기`
  - 관리 종료 식물: `관리 종료된 식물`

## 기록하기 Bottom Sheet

실제 구현:

- `PlantRecordActionSheet`
- 항목:
  - 물주기
  - 메모
  - 사진
  - 영양제: cycle > 0일 때만 표시
  - 분갈이: cycle > 0일 때만 표시
  - 상태
- 메모 sheet:
  - `오늘의 상태를 짧게 남겨보세요.`
- 사진 sheet:
  - 카메라
  - 앨범
- 상태 sheet:
  - 좋음
  - 보통
  - 관심 필요

## 일정 탭

실제 구현:

- 예정된 식물 일정이 없고 최근 활동도 없으면 `예정된 식물 일정이 없습니다.`
- 다가오는 일정:
  - 물주기 예정
  - 영양제 예정
  - 분갈이 예정
- 식물별 due date 기준 정렬
- 최근 활동 5개 표시

## 다이어리 탭

실제 구현:

- 필터:
  - 전체
  - 사진
  - 메모
  - 상태
- 기록 없으면 `아직 다이어리 기록이 없습니다.`
- 사진 기록은 썸네일 표시 및 전체 이미지 preview dialog

## 기록 탭

실제 구현:

- 제목 `기록`
- 필터:
  - 전체
  - 물
  - 영양제
  - 분갈이
  - 메모
  - 상태
  - 사진
- 기록 없으면 icon + `아직 식물 활동 기록이 없습니다.`
- 기록 row:
  - 타입 icon
  - timeline title
  - 사진이면 thumbnail
  - subtitle
  - popup menu
- popup:
  - 메모/상태는 수정 가능
  - 모든 기록 삭제 가능
- 삭제는 `RecordController.deleteAction()` -> repository soft delete 흐름

## 식물사전

실제 구현:

- AppBar `식물사전`
- 검색창 `식물 이름을 검색하세요`
- 오늘의 식물 카드
- quick sections horizontal:
  - 초보 추천
  - 공기정화
  - 인테리어
  - 반려동물 주의
  - 아이 주의
  - 물을 좋아해요
  - 햇빛을 좋아해요
  - 따뜻한 곳 추천
  - 최근 업데이트
  - 인기 식물
- `식물 N종`
- 식물 list
- 검색 결과 없으면 `검색 결과가 없습니다.`

## 식물사전 상세

실제 구현:

- AppBar `식물 정보`
- header:
  - 이미지
  - 식물명
  - 기준 정보 확인 중 또는 type
- 기본 정보:
  - 분류
  - 이름
  - ID
- 설명
- 관리 정보:
  - 물주기
  - 햇빛
  - 수분
  - 온도
- 추천/주의 라벨:
  - 초보 추천
  - 아이 주의
  - 반려동물 주의
  - 공기정화
  - 인테리어
- 관리 팁:
  - 요약
  - 물주기
  - 햇빛
  - 온도
  - 관리
- 커뮤니티 entry:
  - `{식물명} 이야기`
- 이 식물을 키우는 사람들
- 비슷한 식물

## 식물별 커뮤니티

실제 구현:

- `CommunityPostList`
- AppBar에 식물명
- floating edit button
- empty: `아직 이 식물 이야기가 없습니다.`
- 글 목록:
  - 작성자
  - 댓글 수
  - 본문 3줄
- 글 작성 dialog:
  - `식물 이야기 작성`
  - `이 식물에 대한 이야기를 남겨보세요.`

## 커뮤니티 상세

실제 구현:

- AppBar `식물 이야기`
- 작성자면 삭제 icon
- post body:
  - 작성자
  - 본문
  - 작성일
- 댓글 목록
- 댓글 없으면 `아직 댓글이 없습니다.`
- 하단 댓글 입력:
  - `댓글을 입력하세요`
  - send icon

## 계정

실제 구현:

- AppBar `계정`
- 프로필:
  - CircleAvatar
  - display name
  - email 또는 `카카오 로그인 사용자`
- 닉네임 수정
- 알림 switch
- 알림 시간 picker
- 내 식물 공개 switch
- 로그아웃

## AI 적용 관찰

소스 기준으로 가장 자연스러운 삽입 지점은 다음이다.

1. `PlantRecordActionSheet` 상단
   - 이미 기록 유형과 저장 흐름이 모여 있다.
   - 자연어 기록 초안을 넣기 좋다.
2. `RecordHome` 제목 아래
   - 현재 필터 위에 검색/입력 UI가 없다.
   - 전체 기록 자연어 입력 위치로 좋다.
3. `DictionaryDetail` 관리 정보 아래
   - 내 식물 기록과 사전 기준 차이 요약을 넣기 좋다.
4. `CommunityPostList` 글 작성 dialog
   - 최근 내 기록 기반 본문 초안 정도만 적합하다.

