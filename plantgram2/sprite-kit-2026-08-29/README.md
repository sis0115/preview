# 스프라이트 키트

생성 이미지(ChatGPT)를 아바타 에셋으로 쓰기 위한 프롬프트와 도구입니다.
코드로 그리던 `garden-kit`을 대체합니다.

```
PROMPTS.md        시트별 생성 프롬프트 — 공통 규격 + 톤 카드 + 식물·화분·지형·온실·소품
FLUTTER.md        Flutter에서 되는 것과 안 되는 것 (실측 근거)
tone-card.png     프롬프트에 첨부할 색 견본 — 만든 그림에서 뽑은 실제 값
tools/check.py    받은 시트 검사 (투명 배경 · 덩어리 수 · 무채색 · 팔레트 근접도)
tools/slice.py    시트를 낱개 스프라이트로 자름 (알파 연결요소)
tools/pack.py     @3x WebP 변환 + 접지점 기록 manifest 생성
```

## 흐름

```bash
python3 tools/check.py sheets/plants.png                    # 쓸 수 있는 시트인지
python3 tools/slice.py sheets/plants.png sliced/plants 2000 # 낱개로 자르기
python3 tools/pack.py  sliced/plants ../../assets/sprites/plants
```

## 핵심 세 가지

**배경이 투명해야 자릅니다.** 배경이 칠해지면 시트 전체가 한 덩어리가 됩니다.

**식물과 화분을 따로 받아야 합니다.** 한 이미지면 화분 색을 바꿀 때 식물까지
같이 물듭니다. 식물은 흙 선에서 자른 모습으로, 화분은 따로 받습니다.

**톤은 말이 아니라 색값으로 고정합니다.** "테라코타"라고만 하면 매번 다른 주황이
나옵니다. `tone-card.png`를 첨부하고 프롬프트에 `#C85014` 같은 값을 직접 적으세요.
받은 뒤 `check.py`가 기준색과 얼마나 떨어졌는지 재줍니다.
