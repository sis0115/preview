"""온실 한 판을 통째로 받기 위한 기준 그림을 만듭니다.

바닥 타일을 낱개로 받지 않습니다. 온실 전체를 한 장으로 받되, 격자를
우리가 먼저 그려서 보내고 그 위치를 그대로 두라고 시킵니다. 그러면
돌아온 그림에서 칸 좌표를 계산할 필요가 없습니다 - 우리가 정한 좌표가
그대로 살아 있습니다.

같이 나오는 stage_ref.json 에 칸마다의 화면 좌표가 들어 있고, 앱은
그 좌표에 화분 식물을 세우기만 하면 됩니다.
"""
import json
from PIL import Image, ImageDraw

W, H = 1536, 1024
ISO = 1.64
N = 6                       # 6x6 = 36 칸
TW = 150
TH = TW / ISO
CX, CY = W // 2, 600        # 바닥 한가운데

FLOOR = (232, 230, 224)
SEAM = (206, 203, 195)
LAWN = (196, 219, 178)
LAWN_EDGE = (176, 201, 158)
FRAME = (250, 250, 248)
FRAME_LINE = (208, 208, 202)
GLASS = (224, 236, 238)


def cell_center(i, j):
    return (CX + (i - j) * TW / 2, CY + (i + j - (N - 1)) * TH / 2)


def diamond(cx, cy, hw, hh):
    return [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]


def main(out="sheets/stage_ref.png"):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)

    # 바닥 바깥의 잔디 — 온실이 놓인 땅
    pad = 1.5
    dr.polygon(
        diamond(CX, CY, (N / 2 + pad) * TW, (N / 2 + pad) * TH),
        fill=LAWN, outline=LAWN_EDGE,
    )

    # 바닥 격자. 이 선들이 그대로 타일 이음매가 됩니다.
    cells = []
    for i in range(N):
        for j in range(N):
            cx, cy = cell_center(i, j)
            dr.polygon(diamond(cx, cy, TW / 2, TH / 2), fill=FLOOR, outline=SEAM)
            cells.append({"i": i, "j": j, "x": round(cx), "y": round(cy)})

    # 온실 뼈대 — 선만 그립니다. 면을 칠하면 바닥 격자가 가려지는데,
    # 격자가 이 그림의 존재 이유입니다.
    back = cell_center(0, 0)
    left = cell_center(0, N - 1)
    right = cell_center(N - 1, 0)
    front = cell_center(N - 1, N - 1)
    corners = [
        (back[0], back[1] - TH / 2),
        (right[0] + TW / 2, right[1]),
        (front[0], front[1] + TH / 2),
        (left[0] - TW / 2, left[1]),
    ]
    wall, roof = 240, 130
    top = [(x, y - wall) for x, y in corners]
    ridge_a = ((top[0][0] + top[1][0]) / 2, (top[0][1] + top[1][1]) / 2 - roof)
    ridge_b = ((top[2][0] + top[3][0]) / 2, (top[2][1] + top[3][1]) / 2 - roof)

    line = lambda a, b, w=4: dr.line([a, b], fill=FRAME_LINE, width=w)
    for k in range(4):
        line(corners[k], corners[(k + 1) % 4])       # 밑틀
        line(top[k], top[(k + 1) % 4])               # 윗틀
        line(corners[k], top[k], 5)                  # 기둥
    line(ridge_a, ridge_b, 5)                        # 능선
    for t in (top[0], top[1]):
        line(t, ridge_a)
    for t in (top[2], top[3]):
        line(t, ridge_b)

    im.save(out)
    json.dump(
        {"width": W, "height": H, "iso": ISO, "grid": N,
         "tileW": TW, "tileH": round(TH, 1),
         "origin": {"x": CX, "y": CY}, "cells": cells},
        open(out.replace(".png", ".json"), "w"), indent=1,
    )
    print(f"{out}  {W}x{H}")
    print(f"  격자 {N}x{N} · 타일 {TW} x {round(TH)} · 등각 {ISO}:1")
    print(f"  칸 좌표 {len(cells)}개 → {out.replace('.png', '.json')}")


if __name__ == "__main__":
    main()
