"""배경 안내 이미지를 그립니다. 우리 바닥 위에 온실을 그려 달라고 합니다.

바닥만 우리가 그리고 벽·소품은 그림 것을 쓰면 두 그림의 각이 어긋납니다
(해 보고 뒤틀렸습니다). 반대로 **우리가 그린 바닥 격자 위에 온실 전체를**
그려 달라고 하면, 벽과 지붕이 우리 바닥에 맞춰 그려집니다.

타일 200x100 은 조각 크기에서 나왔습니다 - 둥근 화분(180px)이 한 칸에
들어가고, 긴 화단(301px)이 두 칸(300px)에 맞습니다. 조각을 줄이지 않아도
되도록 타일 쪽을 맞췄습니다.

    python3 tools/make_stage_guide.py sheets/stage_guide.png
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1536, 1024
TW, TH = 170, 85                  # 타일. 정확히 2 : 1
N = 5                             # 한 변의 칸 수
CX, CY = 768, 762                 # 바닥 한가운데
WALL = 300                        # 유리벽 높이
ROOF = 150                        # 지붕 마루가 벽 위로 더 올라가는 높이
LAWN = 0.45                       # 바닥 밖 잔디 (칸 단위)

# 조각을 무대에 얹을 때 곱할 배율. 조각 하나만이 아니라 전부 같은 값입니다.
#
# 타일을 조각 크기에 맞추면(200) 특대형 야자가 지붕을 뚫습니다. 그래서
# 온실이 캔버스에 들어가는 크기로 타일을 정하고, 조각 쪽을 줄입니다.
POT_ON_SHEET = 180                # 시트에서 잰 둥근 화분 폭
UNIT = round(TW * .8 / POT_ON_SHEET, 4)

BG = (244, 243, 238)
FLOOR = (233, 232, 226)
SEAM = (176, 178, 170)
EDGE = (120, 124, 116)
GRASS = (206, 224, 196)
GLASS = (150, 176, 190)
INK = (46, 64, 52)
MUTE = (132, 142, 136)
MARK = (232, 106, 30)

FONT = "../app-kit/assets/fonts/{}.otf"


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def dia(cx, cy, hw, hh):
    return [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]


def cell(i, j):
    """칸 (i, j) 의 한가운데. i 는 오른쪽-아래, j 는 왼쪽-아래로 갑니다."""
    x = CX + (i - j) * TW / 2
    y = CY + (i + j - (N - 1)) * TH / 2
    return x, y


def main(out="sheets/stage_guide.png"):
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)

    hw, hh = N * TW / 2, N * TH / 2
    lw, lh = (N + LAWN * 2) * TW / 2, (N + LAWN * 2) * TH / 2

    # 잔디 — 이 바깥은 자유롭게
    dr.polygon(dia(CX, CY, lw, lh), fill=GRASS)
    # 바닥
    dr.polygon(dia(CX, CY, hw, hh), fill=FLOOR)
    for i in range(N):
        for j in range(N):
            x, y = cell(i, j)
            dr.polygon(dia(x, y, TW / 2, TH / 2), outline=SEAM)
    dr.polygon(dia(CX, CY, hw, hh), outline=EDGE)

    top = (CX, CY - hh)
    right = (CX + hw, CY)
    left = (CX - hw, CY)
    bottom = (CX, CY + hh)

    # 뒤쪽 두 변에만 유리벽. 앞은 비워 둡니다 - 식물을 놓을 자리입니다.
    for a, b in ((left, top), (top, right)):
        up_a = (a[0], a[1] - WALL)
        up_b = (b[0], b[1] - WALL)
        dr.polygon([a, b, up_b, up_a], outline=GLASS)
        dr.line([a, up_a], fill=GLASS, width=2)
        dr.line([b, up_b], fill=GLASS, width=2)

    # 지붕 — 뒤 꼭짓점 위로 마루가 솟습니다
    ridge = (top[0], top[1] - WALL - ROOF)
    for corner in (left, right):
        dr.line([(corner[0], corner[1] - WALL), ridge], fill=GLASS, width=2)
    dr.line([(top[0], top[1] - WALL), ridge], fill=GLASS, width=2)

    # 앞 두 변은 비워 둔다는 표시
    for a, b in ((left, bottom), (bottom, right)):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dr.line([a, b], fill=MARK, width=3)
    dr.text((CX, bottom[1] - 26), "앞쪽 두 변 — 기둥도 벽도 두지 마세요",
            font=font(15, True), fill=MARK, anchor="ms")
    dr.text((CX, CY + 8), "바닥 안은 비워 두세요\n화분과 선반은 프로그램이 올립니다",
            font=font(16, True), fill=(150, 158, 148), anchor="mm", align="center")

    dr.text((24, 14), "배경 안내 — 이 바닥 위에 온실을 그려 주세요",
            font=font(21, True), fill=INK)
    dr.text((24, 42),
            f"타일 {TW}×{TH} (정확히 2:1) · {N}×{N} 칸 · "
            "바닥 타일의 이음선이 이 격자선과 정확히 겹치게 그려 주세요",
            font=font(14), fill=MUTE)
    dr.text((24, 64),
            "격자선 위치는 한 픽셀도 옮기지 마세요. 그 위에 색·질감·유리벽·"
            "지붕·잔디를 입혀 주세요.        "
            "소품은 바닥 바깥이나 벽 쪽에만 — 바닥 안은 비워 두세요",
            font=font(14), fill=MUTE)

    dr.text((left[0] - 10, left[1] - WALL - 30), "유리벽", font=font(14, True),
            fill=(96, 128, 146), anchor="rs")
    dr.text((CX + lw + 30, CY + 30), "이 바깥은 자유\n잔디 · 길 · 나무 · 하늘",
            font=font(14), fill=(110, 140, 100), align="left")

    spec = {
        "wallTop": round(top[1] - WALL), "ridge": round(ridge[1]),
        "width": W, "height": H, "tileW": TW, "tileH": TH, "n": N,
        "originX": CX, "originY": CY,
        "corners": {"top": list(top), "right": list(right),
                    "bottom": list(bottom), "left": list(left)},
        "cells": [{"i": i, "j": j, "x": round(cell(i, j)[0]),
                   "y": round(cell(i, j)[1])}
                  for i in range(N) for j in range(N)],
    }
    spec["unit"] = UNIT
    im.save(out)
    json.dump(spec, open(out.replace(".png", ".json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"{out} · 바닥 {N}x{N} · 타일 {TW}x{TH} · "
          f"바닥 {round(2 * hw)}x{round(2 * hh)} · 조각 배율 {UNIT}")
    print(f"  유리벽 위끝 y={round(top[1] - WALL)} · 지붕 마루 y={round(ridge[1])}")


if __name__ == "__main__":
    main(*sys.argv[1:])
