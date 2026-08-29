# 스프라이트 생성 프롬프트 팩

ChatGPT로 만든 그림을 아바타 에셋으로 쓰기 위한 프롬프트 모음입니다.
코드로 그리는 판(garden-kit)을 대체합니다.

가장 중요한 규칙 두 가지부터.

**1. 배경이 투명해야 합니다.** 배경이 칠해져 있으면 시트 전체가 한 덩어리가 되어
낱개로 못 자릅니다. 모든 프롬프트에 `transparent background` 를 넣으세요.

**2. 식물과 화분을 따로 만들어야 합니다.** 한 장에 같이 그리면 화분을 못 바꿉니다.
색을 바꿀 때도 식물까지 같이 물듭니다 (실험으로 확인했습니다).
식물은 흙 선에서 자른 모습으로, 화분은 따로 받습니다.

---

## 0. 공통 규격 — 모든 프롬프트 끝에 붙입니다

```
Style: isometric 2:1 dimetric projection, camera elevated ~30 degrees, viewed from
front-upper-left. Flat vector illustration with soft cel shading, clean crisp edges,
no outlines. Single light source from the upper left; one soft contact shadow
directly beneath each object.

Layout: arranged on an evenly spaced grid, each item fully separated with at least
60 pixels of empty space around it. Every item drawn at the same camera angle and
the same scale relationship.

Background: fully transparent (PNG with alpha). No background color, no gradient,
no ground plane, no surface, no table. No text, no labels, no numbers, no watermark.

Output: 1536x1024 PNG with transparency.
```

> **스타일 고정 요령** — 이미 마음에 드는 그림이 있으면 그걸 첨부하고
> `Match the art style, color palette, shading and camera angle of the attached
> image exactly.` 를 앞에 붙이세요. 말로 설명하는 것보다 훨씬 정확합니다.

---

## 1. 식물 — 화분 없이

가장 중요한 시트입니다. **화분 없이** 받아야 화분을 갈아 끼울 수 있습니다.

```
A sprite sheet of 12 houseplants, each drawn WITHOUT any pot or container.
Each plant is cut off cleanly at the soil line — show only the stems and leaves,
nothing below. No pot, no soil, no roots.

Plants: monstera deliciosa, bird of paradise (strelitzia nicolai), lucky bamboo,
areca palm, silver dollar eucalyptus, dieffenbachia, jade plant (crassula ovata),
fiddle leaf fig, snake plant (sansevieria), pothos trailing vine, boston fern,
rubber plant (ficus elastica).

Each plant keeps its real growth habit — monstera has fenestrated split leaves on a
thick climbing stem, eucalyptus has round leaves in opposite pairs along the stem,
snake plant has upright banded blades, pothos trails downward.

[공통 규격 붙이기]
```

### 성장 단계

레벨에 따라 자라야 하므로 종마다 4단계가 필요합니다. **한 종씩** 따로 뽑으세요
(한 시트에 여러 종 × 여러 단계를 넣으면 스타일이 흔들립니다).

```
A sprite sheet showing ONE monstera deliciosa plant at 4 growth stages, left to right:
(1) seedling — a single small entire heart-shaped leaf, no splits
(2) young — 3 leaves, shallow edge splits beginning
(3) mature — 5 leaves, deep splits, one hole appearing
(4) full — 7 leaves on a thick stem, deeply split with holes in rows

All four drawn WITHOUT pots, cut at the soil line, same camera angle, same style.
The plant gets taller and fuller from left to right.

[공통 규격 붙이기]
```

---

## 2. 화분 — 회색으로

화분은 **무채색(밝은 회색)** 으로 받으세요. 앱에서 색을 곱해 원하는 색으로 바꿉니다
(음영이 그대로 보존되는 것을 실험으로 확인했습니다). 그래야 화분 색 커스텀이
지금처럼 남습니다.

```
A sprite sheet of 10 empty plant containers, all in NEUTRAL LIGHT GRAY with no
color tint at all — pure grayscale, so they can be recolored later. Keep the
shading and highlights.

Containers: standard tapered flower pot, low wide bowl, tall cylinder pot,
round-bellied urn, pot with a thick rim, square modern planter, long rectangular
window box, wooden trough with legs, woven basket, glass jar.

Each container is EMPTY — show the dark soil surface inside, but no plant.

[공통 규격 붙이기]
```

> 테라코타·화이트 세라믹처럼 **재질이 확실한 화분**은 회색 말고 그 색 그대로 한 세트
> 더 받는 편이 예쁩니다. 회색 세트는 커스텀용, 색 세트는 기본값용입니다.

---

## 3. 지형 타일

정원 바닥입니다. **정확한 마름모**여야 이어 붙습니다.

```
A sprite sheet of 8 isometric floor tiles. Each tile is a perfect rhombus (diamond)
with a 2:1 width-to-height ratio, drawn so that tiles placed edge to edge tile
seamlessly with no gaps or seams.

Tiles: dark garden soil, short green grass, light gravel, wooden deck planks,
pale stone paving, red brick, mulch bark chips, shallow water.

Each tile has a slight thickness at the front edge (about 8% of the tile height)
so it reads as a raised slab. All 8 tiles are exactly the same size and shape.

[공통 규격 붙이기]
```

---

## 4. 온실 구조 — 조립식

한 덩어리로 받으면 못 씁니다. **부품으로** 받아 코드로 조립합니다.

```
A sprite sheet of 10 modular greenhouse building parts in a white-painted frame with
pale glass panels. Parts must fit together like a kit:

wall panel facing left, wall panel facing right, corner post, door panel (closed),
door panel (open), roof slope facing left, roof slope facing right, roof ridge cap,
gable end panel, low foundation wall section.

All parts share the same wall height and the same 2:1 isometric angle so they align
when assembled. Glass is pale blue-white and slightly transparent with a soft
diagonal highlight.

[공통 규격 붙이기]
```

---

## 5. 소품

```
A sprite sheet of 12 garden props: watering can, wooden wheelbarrow, potting bench,
wooden shelf unit with 3 levels, seed starting tray with small sprouts, hand trowel
and fork pair, coiled hose, wooden sign board (blank), hanging lantern, stack of
empty terracotta pots, bag of soil, small stone border piece.

[공통 규격 붙이기]
```

---

## 6. 받은 다음 — 자르고 앱에 넣기

```bash
# 1) 시트를 낱개로 자릅니다 (투명 배경이면 자동으로 덩어리를 찾습니다)
python3 tools/slice.py sheets/plants.png sliced/plants 2000

# 2) 앱에 넣을 크기·형식으로 변환합니다 (@3x WebP + 접지점 기록)
python3 tools/pack.py sliced/plants ../../assets/sprites/plants
```

`pack.py`가 만드는 `manifest.json`에는 스프라이트마다 **접지점**(anchorX, anchorY)이
들어갑니다. 아이소 격자에 앉힐 때 이 점을 타일 중심에 맞추면 식물이 화분 위에,
화분이 타일 위에 정확히 놓입니다.

자른 뒤에는 **이름을 사람이 붙여야 합니다** — 자동으로 나오는 `s00`, `s01`은
왼쪽 위부터의 순서일 뿐이라 어떤 종인지 모릅니다. `index.json`을 보고
`monstera_s4`, `pot_bowl` 처럼 바꾸세요.

---

## 7. 잘 안 나올 때

| 증상 | 원인 | 프롬프트 수정 |
|---|---|---|
| 낱개로 안 잘림 | 배경이 칠해짐 | `transparent background, no background color` 를 앞쪽에 다시 |
| 두 식물이 한 덩어리 | 간격이 좁음 | `at least 80 pixels of empty space around each item` |
| 시트마다 톤이 다름 | 말로만 설명 | 마음에 드는 시트를 **첨부**하고 `match the attached image exactly` |
| 화분이 색을 띔 | 회색 지시 약함 | `pure grayscale, zero saturation, no color tint whatsoever` |
| 타일이 안 이어짐 | 마름모가 부정확 | `perfect rhombus, exactly 2:1 width to height, seamlessly tileable` |
| 잎이 사실적으로 나옴 | 스타일 지시 부족 | `flat vector illustration, cel shading, no gradients, no photorealism` |
