"""바닥 타일을 '그려 달라' 대신 '이 그림을 다시 그려 달라' 로 받기 위한
기준 이미지를 만듭니다.

타일은 이어 붙였을 때 이음매가 맞아야 합니다. 낱개로 따로 받으면
각도도 크기도 매번 달라져 맞은 적이 없습니다. 대신 우리가 정확한
기하로 배치한 그림을 보내고 재질만 입혀 달라고 하면, 각도와 크기는
우리가 정한 채로 돌아옵니다.

재질마다 2x2 로 놓아 이어 붙는 모습까지 함께 보여줍니다. 받은 뒤에는
각 묶음의 왼쪽 위 한 칸만 오려내면 됩니다 — 위치를 알고 있으니까요.
"""
import json
from PIL import Image, ImageDraw

ISO = 1.64
TW = 168
TH = TW / ISO
THICK = round(TH * .08)      # 옆면은 윗면 높이의 8%
GAP_X, GAP_Y = 42, 54
COLS = 4

# 재질과 그 자리에 칠할 바탕색. 색은 목표 톤(연하고 밝게)에 맞춥니다.
MATERIALS = [
    ("tile_soil", (156, 133, 113)),
    ("tile_grass", (166, 199, 149)),
    ("tile_gravel", (203, 199, 190)),
    ("tile_deck", (203, 176, 143)),
    ("tile_stone", (222, 217, 205)),
    ("tile_brick", (206, 152, 124)),
    ("tile_mulch", (168, 143, 121)),
    ("tile_water", (176, 205, 214)),
]


def shade(c, k):
    return tuple(min(255, round(v * k)) for v in c)


def diamond(dr, cx, cy, fill):
    hw, hh = TW / 2, TH / 2
    dr.polygon(
        [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)],
        fill=fill, outline=shade(fill, .93),
    )


def patch(dr, ox, oy, color):
    """한 재질을 2x2 로 깔고 앞쪽 옆면을 붙입니다."""
    cells = sorted([(i, j) for i in range(2) for j in range(2)],
                   key=lambda c: c[0] + c[1])
    for i, j in cells:
        cx = ox + (i - j) * TW / 2
        cy = oy + (i + j) * TH / 2
        diamond(dr, cx, cy, color)
    # 앞쪽 두 변에만 두께를 붙입니다
    for i, j in [(1, 0), (1, 1), (0, 1)]:
        cx = ox + (i - j) * TW / 2
        cy = oy + (i + j) * TH / 2
        hw, hh = TW / 2, TH / 2
        dr.polygon(
            [(cx - hw, cy), (cx, cy + hh), (cx + hw, cy),
             (cx + hw, cy + THICK), (cx, cy + hh + THICK), (cx - hw, cy + THICK)],
            fill=shade(color, .86),
        )


def main(out="sheets/floor_ref.png"):
    pw = TW * 2 + GAP_X
    ph = TH * 2 + THICK + GAP_Y
    rows = (len(MATERIALS) + COLS - 1) // COLS
    W = round(COLS * pw + GAP_X)
    H = round(rows * ph + GAP_Y * 1.5)
    im = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)

    index = []
    for n, (name, color) in enumerate(MATERIALS):
        r, c = divmod(n, COLS)
        ox = GAP_X + c * pw + TW / 2 + TW / 2
        oy = GAP_Y + r * ph + TH / 2
        patch(dr, ox, oy, color)
        # 나중에 오려낼 칸은 각 묶음의 (0,0) 입니다
        index.append({"name": name, "cx": round(ox), "cy": round(oy),
                      "tileW": TW, "tileH": round(TH)})

    im.save(out)
    json.dump({"iso": ISO, "tileW": TW, "tileH": round(TH), "tiles": index},
              open(out.replace(".png", ".json"), "w"), indent=1)
    print(f"{out}  {W}x{H}  재질 {len(MATERIALS)}종")
    print(f"  타일 {TW} x {round(TH)}  (등각 {ISO}:1, 옆면 {THICK}px)")


if __name__ == "__main__":
    main()
