# 플랫폼 선택 분석 — Flutter vs 네이티브 (게임성 기능 중심)

> 2026-08 조사. 판단 기준: 비용이 아니라 **"우리 기능(아바타 꾸미기·정원·게임 이벤트)을 구현할 수 있는가"**와 **Flutter 생태계의 현재 건강 상태**.

---

## 1. Flutter는 지금도 살아있는가 — 결론: 활발히 성장 중

| 지표 | 2026년 현재 상태 |
|---|---|
| 릴리스 | 최신 stable **3.44** (2026-05), 연 4회(2·5·8·11월) 정기 릴리스 유지, 3.47 예정 |
| 2026 로드맵 | Android Impeller 렌더러 전환 완료, Web은 WebAssembly 기본화, Material/Cupertino 패키지 분리(더 빠른 릴리스), LG webOS TV 공식 SDK, Dart/Flutter MCP 서버 등 AI 도구 |
| 개발자 만족도 | 공식 Q2 2026 설문(3,500+명) **긍정 93%** |
| 채택 | iOS 상위 1만 앱 중 Flutter 1,184개 (RN 1,350개와 대등), 크로스플랫폼 앱 다운로드의 38% |
| 프로덕션 사례 | BMW(myBMW), Alibaba Xianyu, Toyota, ByteDance, talabat, GE 가전 |
- "Flutter is dying" 논란은 2024~25년 구글 레이오프 때 있었으나, 2026년 시점 데이터는 성숙기 진입으로 결론. 정기 릴리스·로드맵·서베이가 모두 정상 가동 중

## 2. 핵심 검증 — "게임성은 네이티브 라이브러리가 더 낫지 않나?"

**전제 점검이 먼저**: 우리 게임성은 "게임 엔진"이 아니라 **모션 리치 UI** 문제다. 물리·3D·월드가 아니라 ① 레이어 조합 아바타 ② 배치형 정원 씬 ③ 셀레브레이션 연출. 이 영역의 산업 표준 도구는 플랫폼 내장 라이브러리가 아니라 **크로스플랫폼 도구(Lottie, Rive)**다.

### 네이티브 진영의 실상 (2026)
| 플랫폼 | 2D 게임/모션 프레임워크 | 상태 |
|---|---|---|
| iOS | SpriteKit | 공식 지원은 유지되나, **자매 프레임워크 SceneKit이 WWDC 2025에서 deprecated** → 커뮤니티에서 SpriteKit도 시간문제라는 우려 확산, 후속 대체재 없음. 신규 프로젝트 기반으로 삼기엔 리스크 |
| Android | (해당 없음) | **1st-party 2D 게임 프레임워크 자체가 없음.** Jetpack Compose 애니메이션 API가 전부 |
| 공통 | Lottie / Rive 런타임 | 네이티브에서도 결국 이 도구를 씀 — 토스의 셀레브레이션도 Lottie 계열 |
→ "자기 플랫폼 라이브러리가 잘 되어 있다"는 가정은 **iOS 절반만 맞고(그마저 미래 불투명), Android는 틀림**. 네이티브 2벌로 가도 게임성 구현의 실제 도구는 Flutter와 동일한 Lottie/Rive가 된다.

### 우리 기능별 Flutter 구현 경로
| 기능 | 구현 스택 | 평가 |
|---|---|---|
| 아바타 레이어 조합 (종 베이스 × 화분 × 소품) | Flutter 기본 (Stack + SVG/CustomPaint) | 순수 UI 조합 — Flutter 주특기, 네이티브 대비 열세 없음 |
| 아바타 상태·성장 애니메이션 (시듦, 물 받고 기뻐함, 성장 단계 전환) | **Rive** (rive 공식 패키지, State Machine) | 리깅된 캐릭터를 상태 기반으로 구동 — Duolingo류 캐릭터 UX의 표준 도구. 에디터에서 디자이너가 직접 수정 가능 |
| 정원 씬 (배치, 드래그, 탭 인터랙션, 시간대 연출) | 1차: 순수 Flutter (Stack + Draggable + AnimatedPositioned) / 확장: **Flame** GameWidget 임베드 | Flame은 앱 속 한 화면에만 게임 루프를 넣을 수 있음(전체 앱을 게임으로 만들 필요 없음). flame_rive로 Rive 캐릭터를 씬 안에서 구동 가능 |
| 레벨업 셀레브레이션 (폭죽·컨페티) | **Lottie**(공식 품질 패키지) / confetti / Rive | 토스가 쓰는 것과 같은 계열 도구. After Effects 산출물 그대로 사용 |
| 물결 게이지·카운트업 등 마이크로 인터랙션 | Flutter 기본 애니메이션 | 레거시에서 이미 Flutter로 구현했던 것들 |
| 렌더링 성능 | **Impeller** (2026 Android 전환 완료) | 셰이더 컴파일 jank 제거 — 애니메이션 heavy UI를 위해 설계된 렌더러 |

### Flutter가 불리한 경우 (해당 여부 점검)
- **3D** — Flutter 3D는 아직 초기(Fluorite 등 실험 단계). → 우리는 2D 확정이므로 무관
- **본격 게임**(물리 월드, 대규모 씬) — Unity/Godot 영역. → 우리 정원은 UI+연출이지 게임 월드가 아님. 필요해져도 Flame 2D(Forge2D 물리 포함)로 커버 가능
- 위젯·워치 등 OS 딥 통합 — 네이티브 모듈 필요(WidgetKit/Glance). → 어차피 네이티브 2벌로 가도 각각 따로 만들어야 하는 부분. Flutter 본체와 무관

## 3. 결론 및 권고

**Flutter 단일 코드베이스로 간다.** 근거:
1. 게임성 3요소(아바타·정원·셀레브레이션)의 실질 도구는 Rive/Lottie/Flame — 전부 Flutter 1급 지원이며, 네이티브로 가도 같은 도구를 쓰게 됨
2. 네이티브 진영이 오히려 리스크: iOS SpriteKit 미래 불투명, Android는 대응 프레임워크 부재
3. Flutter는 2026년 현재 정기 릴리스·93% 만족도·대형 프로덕션 사례로 건강 입증
4. 우리 팀 자산(플랜트그램 1·2 Flutter 경험) 재활용

**확정 기술 스택 (게임성 레이어)**
```
Flutter 3.4x (Impeller)
 ├─ 아바타: SVG 레이어 조합 + Rive State Machine (성장/상태/반응)
 ├─ 정원 씬: M3 1차는 순수 Flutter → 연출 욕심나면 Flame GameWidget 승격
 ├─ 셀레브레이션: Lottie (+confetti)
 └─ 네이티브 모듈: 홈 위젯(WidgetKit/Glance), 소셜 로그인 SDK
```

**리스크 헤지**
- Rive 에디터로 아바타를 제작하면 iOS/Android/웹 네이티브 런타임도 있어, 만에 하나 플랫폼 전환하더라도 **아트 자산은 100% 재사용** 가능
- 정원 씬을 위젯 트리와 분리된 모듈로 설계해 Flame 승격/교체가 국소 변경이 되도록 함

## 4. 참고 출처
- Flutter 3.44 릴리스·2026 로드맵: blog.flutter.dev (What's new in Flutter 3.41 / Flutter & Dart's 2026 roadmap)
- Q2 2026 공식 서베이(만족도 93%): flutter.dev/blog/flutter-q2-2026-survey
- 채택 통계·사례: The Fix "Is Flutter Dying Out? The Surprising 2026 Industry Verdict", Tomáš Repčík "My take on Flutter in 2026"
- Flame/Rive: flame-engine GitHub, pub.dev/packages/flame, Synfinity Dynamics "Flutter Game Development in 2026"
- SceneKit deprecated·SpriteKit 우려: Apple Developer Forums, Paul Hudson (WWDC 2025)
