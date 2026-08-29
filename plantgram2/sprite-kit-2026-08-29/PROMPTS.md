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

## 0-B. 톤 카드 — 이미 만든 그림에서 뽑은 실제 색

말로 "테라코타"라고 하면 매번 다른 주황이 나옵니다. **뽑아낸 색값을 프롬프트에 직접
적고**, `tone-card.png`를 같이 첨부하세요. 이게 톤을 맞추는 가장 확실한 방법입니다.

| | 값 | 쓰임 |
|---|---|---|
| 화분 하이라이트 | `#DC641E` | 좌상단 빛 받는 면 |
| **화분 기본** | **`#C85014`** | 몸통 |
| 화분 중간 | `#BE4614` | 몸통 그늘 쪽 |
| 화분 그림자 | `#A03C14` | 오른쪽 면·바닥 |
| 화분 림 | `#C8823C` | 테두리 윗면 |
| 흙 밝은 | `#462814` | 흙 표면 빛 쪽 |
| 흙 기본 | `#3C2814` | 흙 표면 |
| 흙 어두운 | `#1E140A` | 화분 안쪽 그늘 |
| 잎 밝은 | `#78BE1E` | 새잎·빛 받는 잎 |
| 잎 어두운 | `#328214` | 묵은 잎·뒤쪽 잎 |

**명암 대비는 약 4:1** 입니다 (가장 밝은 면 ÷ 가장 어두운 면). 이보다 평평하면
다른 시트와 안 붙고, 이보다 세면 튑니다.


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

## 2. 화분 — 두 세트로 받습니다

화분은 **두 번** 받아야 합니다. 이유가 다릅니다.

- **색 세트** — 기본 화분. 톤 카드 색 그대로. 그대로 씁니다.
- **무채색 세트** — 커스텀용. 앱에서 색을 곱해 원하는 색으로 바꿉니다.
  색이 들어간 화분에 곱하면 원래 색과 섞여 탁해지므로 따로 받아야 합니다.

### 2-A. 색 세트 (기본 화분)

```
Match the art style, shading, camera angle and color palette of the attached
images exactly — same isometric angle, same soft cel shading, same edge quality.

A sprite sheet of 10 EMPTY plant containers. No plants, no leaves, nothing growing —
each container shows only the dark soil surface inside.

Containers, all drawn at the same scale as if they would hold a medium houseplant:
1. standard tapered terracotta flower pot with a raised rim
2. low wide terracotta bowl, about half the height of pot 1
3. tall terracotta cylinder pot
4. round-bellied terracotta urn
5. white glazed ceramic pot
6. pale mint green glazed ceramic pot
7. dark charcoal gray concrete cube planter
8. long rectangular terracotta window box
9. wooden trough with short legs
10. small clear glass jar

Terracotta color: base #C85014, highlight #DC641E on the upper-left face,
shadow #A03C14 on the lower-right face, rim top edge #C8823C.
Soil surface: #3C2814 with darker #1E140A in the shaded inner edge.
Keep the light-to-dark contrast at roughly 4:1 — clearly shaded, not flat.

[공통 규격 붙이기]
```

### 2-B. 무채색 세트 (커스텀용)

같은 화분 10종을 **색만 빼서** 한 번 더 받습니다.

```
The same 10 containers as before, in exactly the same shapes, sizes, camera angle
and lighting — but rendered in PURE GRAYSCALE. Zero saturation, no color tint of
any kind, not even a warm or cool cast. Only white, grays and black.

Keep all the shading, highlights and shadows exactly as in the color version — the
gray values must carry the same light-to-dark contrast, because these will be
recolored programmatically by multiplying a color over them.

The soil surface inside stays dark gray.

[공통 규격 붙이기]
```

> 무채색 세트가 제대로 나왔는지 확인하는 법 — 픽셀을 찍었을 때 R·G·B가 **같은 값**이어야
> 합니다. 조금이라도 주황기가 남으면 곱했을 때 색이 틀어집니다.
> 안 되면 `zero saturation, R=G=B for every pixel` 을 추가하세요.

### 2-C. 화분과 식물의 크기 맞추기

화분 시트와 식물 시트를 따로 받으면 **크기가 안 맞습니다.** 프롬프트에 기준을 박습니다.

```
Scale reference: the standard tapered pot (container 1) is 100 units wide and
55 units tall. Draw every other container relative to that — the low bowl is
110 wide and 32 tall, the tall cylinder is 84 wide and 96 tall, and so on.
```

식물 시트에도 같은 기준을 넣습니다.

```
Scale reference: each plant is drawn as it would look planted in a pot that is
100 units wide — the foliage spans about 150-180 units wide and rises about
120-200 units above the soil line depending on the species.
```

이래도 어긋나면 `pack.py`가 기록하는 접지점으로 코드에서 맞출 수 있으니, 완벽할
필요는 없습니다.

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

Tone: match the attached tone card. Soil tiles use #3C2814 with #462814 highlights.
Grass uses the leaf greens #78BE1E and #328214. Terracotta brick uses #C85014.
Keep the same 4:1 light-to-dark contrast as the plant and pot sheets — the ground
must sit quietly under the plants, so keep tile shading slightly softer than the
plants but in the same color family.

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

Tone: match the attached tone card. The white frame is a warm off-white, not pure
white, so it sits with the terracotta. Any wood is #A03C14 shifted toward brown.
The greenhouse is a backdrop — keep it lower contrast than the plants so the plants
stay the subject.

[공통 규격 붙이기]
```

---

## 5. 소품

```
A sprite sheet of 12 garden props: watering can, wooden wheelbarrow, potting bench,
wooden shelf unit with 3 levels, seed starting tray with small sprouts, hand trowel
and fork pair, coiled hose, wooden sign board (blank), hanging lantern, stack of
empty terracotta pots, bag of soil, small stone border piece.

Tone: match the attached tone card. Terracotta items use #C85014 / #DC641E / #A03C14.
Wood is a warm brown in the same family. Metal is a desaturated gray-green so it
does not compete with the plants.

[공통 규격 붙이기]
```

---

## 6. 받은 다음 — 자르고 앱에 넣기

```bash
# 0) 받은 시트가 쓸 수 있는지 먼저 검사합니다
python3 tools/check.py sheets/pots_gray.png --gray

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
