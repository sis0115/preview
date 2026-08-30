"""온실 한 판을 통째로 받기 위한 기준 그림.

바닥 타일을 낱개로 받지 않습니다. 온실 전체를 한 장으로 받되 격자를
우리가 먼저 그려 보내고 그 위치를 그대로 두라고 시킵니다. 돌아온
그림에서 칸 좌표를 추정할 필요가 없습니다.

세 가지가 이 그림의 전제입니다.

1. 등각은 2:1 입니다. 앱 화면의 잔디 마름모 왼쪽 변 기울기가 정확히
   0.5 였고, 예전 garden-kit 의 격자 상수도 78 x 39 로 2:1 이었습니다.
2. 앞쪽 두 벽과 앞 기둥은 그리지 않습니다. 거기 식물이 놓이는데 기둥이
   앞을 가로지르면 식물이 기둥에 걸린 것처럼 보입니다.
3. 바닥만 덩그러니 두지 않습니다. 잔디, 진입로, 관목 자리를 함께
   잡아 줘야 판때기로 보이지 않습니다.
"""
import json
from PIL import Image, ImageDraw

W, H = 1536, 1024
ISO = 2.0                    # 앱 실측값
N = 6
TW = 168
TH = TW / ISO                # 84
CX, CY = W // 2, 600

LAWN = (198, 220, 180)
LAWN_LINE = (176, 201, 158)
PATH = (226, 221, 208)
PATH_LINE = (203, 197, 184)
FLOOR = (236, 234, 228)
SEAM = (205, 202, 194)
FRAME = (198, 198, 192)
SHRUB = (176, 205, 160)


def center(i, j):
    return (CX + (i - j) * TW / 2, CY + (i + j - (N - 1)) * TH / 2)


def dia(cx, cy, hw, hh):
    return [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]


def main(out="sheets/stage_ref.png"):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)

    # 잔디 — 온실이 놓인 땅. 바닥보다 두 칸 넓게.
    dr.polygon(dia(CX, CY, (N / 2 + 2) * TW, (N / 2 + 2) * TH),
               fill=LAWN, outline=LAWN_LINE)

    # 진입로 — 앞 꼭짓점에서 온실 입구까지. 판때기로 보이지 않게 합니다.
    for k in range(1, 3):
        cx, cy = center(N - 1 + k, N - 1 + k)
        dr.polygon(dia(cx, cy, TW / 2, TH / 2), fill=PATH, outline=PATH_LINE)

    # 관목 자리 — 네 귀퉁이 바깥. 위치만 잡아 줍니다.
    for i, j in [(-2, 2), (2, -2), (N + 1, N - 3), (N - 3, N + 1)]:
        cx, cy = center(i, j)
        dr.ellipse([cx - 26, cy - 20, cx + 26, cy + 14], fill=SHRUB, outline=LAWN_LINE)

    # 바닥 격자 6x6. 이 선들이 그대로 타일 이음매가 됩니다.
    cells = []
    for i in range(N):
        for j in range(N):
            cx, cy = center(i, j)
            dr.polygon(dia(cx, cy, TW / 2, TH / 2), fill=FLOOR, outline=SEAM)
            cells.append({"i": i, "j": j, "x": round(cx), "y": round(cy)})

    # 온실 뼈대 — 선만. 면을 칠하면 격자가 가려집니다.
    back = center(0, 0)
    right = center(N - 1, 0)
    front = center(N - 1, N - 1)
    left = center(0, N - 1)
    foot = [
        (back[0], back[1] - TH / 2),      # 0 뒤
        (right[0] + TW / 2, right[1]),    # 1 오른쪽
        (front[0], front[1] + TH / 2),    # 2 앞  ← 기둥 없음
        (left[0] - TW / 2, left[1]),      # 3 왼쪽
    ]
    wall, roof = 236, 132
    top = [(x, y - wall) for x, y in foot]
    ridge_back = ((top[0][0] + top[1][0]) / 2, (top[0][1] + top[1][1]) / 2 - roof)
    ridge_front = ((top[2][0] + top[3][0]) / 2, (top[2][1] + top[3][1]) / 2 - roof)

    def line(a, b, w=4):
        dr.line([a, b], fill=FRAME, width=w)

    # 뒤쪽 두 벽만 세웁니다 — 앞 두 면과 앞 기둥은 그리지 않습니다.
    for k in (0, 1, 3):
        line(foot[k], top[k], 5)
    line(foot[3], foot[0])
    line(foot[0], foot[1])
    line(top[3], top[0])
    line(top[0], top[1])
    # 앞쪽은 바닥 테두리만 남겨 경계를 알립니다
    line(foot[1], foot[2], 3)
    line(foot[2], foot[3], 3)
    # 지붕 — 뒤쪽만. 앞 모서리(top[2])로 가는 선은 그리지 않습니다.
    # 그 선들이 바닥을 가로질러 격자를 읽기 어렵게 만듭니다.
    line(ridge_back, ridge_front, 5)
    for t in (top[0], top[1], top[3]):
        line(t, ridge_back if t is not top[3] else ridge_front)

    im.save(out)
    json.dump({"width": W, "height": H, "iso": ISO, "grid": N,
               "tileW": TW, "tileH": TH,
               "origin": {"x": CX, "y": CY}, "cells": cells},
              open(out.replace(".png", ".json"), "w"), indent=1)
    print(f"{out}  {W}x{H}")
    print(f"  격자 {N}x{N} · 타일 {TW} x {round(TH)} · 등각 {ISO}:1")
    print(f"  앞 기둥·앞 두 벽 없음 · 진입로 2칸 · 관목 자리 4곳")


if __name__ == "__main__":
    main()
