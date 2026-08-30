"""예제 한 벌을 한 장으로 받기 위한 기준 그림.

위쪽은 온실 무대(바닥 격자 포함), 아래쪽은 잘라 쓸 조각들입니다.
자를 자리와 접합점을 미리 그려 보내므로, 받은 뒤에 찾을 필요가 없습니다.

그림자는 요청하지 않습니다. 부드러운 타원이라 코드로 그리는 편이
정확하고, 화분마다 폭을 맞출 수 있습니다.
"""
import json
from PIL import Image, ImageDraw

W, H = 1536, 1024
STAGE_H = 640                 # 위쪽: 온실 무대
STRIP_Y = STAGE_H             # 아래쪽: 조각들
CELLS = 6
CW = W // CELLS               # 256
CH = H - STRIP_Y              # 384

ISO = 2.0
N = 4                         # 무대 격자 4x4
TW = 170
TH = TW / ISO                 # 85
CX, CY = W // 2, 373         # 지붕 꼭대기와 잔디 앞끝이 무대 안에 들어오는 높이

MARK = (232, 120, 40)
SOFT = (245, 200, 168)
GUIDE = (214, 214, 210)
FLOOR = (236, 234, 228)
SEAM = (204, 201, 193)
LAWN = (200, 221, 183)
FRAME = (196, 196, 190)

# 아래 줄에 놓을 조각. (id, 종류, 흙 폭, 심는 자리 수)
PIECES = [
    ("pot_terracotta", "pot", 120, 1),
    ("pot_white", "pot", 120, 1),
    ("bed_wood", "pot", 210, 2),
    ("monstera", "plant", 0, 0),
    ("strelitzia", "plant", 0, 0),
    ("bamboo", "plant", 0, 0),
]

POT_ANCHOR_Y = 0.34
PLANT_ANCHOR_Y = 0.90


def dia(cx, cy, hw, hh):
    return [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]


def main(out="sheets/kit_ref.png"):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    meta = {"width": W, "height": H, "iso": ISO,
            "stage": {"x": 0, "y": 0, "w": W, "h": STAGE_H,
                      "grid": N, "tileW": TW, "tileH": TH,
                      "originX": CX, "originY": CY, "cells": []},
            "pieces": []}

    # ── 무대 ───────────────────────────────────────────────
    dr.polygon(dia(CX, CY, (N / 2 + .9) * TW, (N / 2 + .9) * TH),
               fill=LAWN, outline=(178, 203, 160))
    for i in range(N):
        for j in range(N):
            cx = CX + (i - j) * TW / 2
            cy = CY + (i + j - (N - 1)) * TH / 2
            dr.polygon(dia(cx, cy, TW / 2, TH / 2), fill=FLOOR, outline=SEAM)
            meta["stage"]["cells"].append({"i": i, "j": j,
                                           "x": round(cx), "y": round(cy)})

    back = (CX, CY - (N - 1) * TH / 2 - TH / 2)
    right = (CX + N * TW / 2, CY)
    front = (CX, CY + (N - 1) * TH / 2 + TH / 2)
    left = (CX - N * TW / 2, CY)
    foot = [back, right, front, left]
    wall, roof = 130, 60
    top = [(x, y - wall) for x, y in foot]
    rb = ((top[0][0] + top[1][0]) / 2, (top[0][1] + top[1][1]) / 2 - roof)
    rf = ((top[2][0] + top[3][0]) / 2, (top[2][1] + top[3][1]) / 2 - roof)

    def line(a, b, w=4):
        dr.line([a, b], fill=FRAME, width=w)

    # 앞 기둥과 앞 두 벽은 그리지 않습니다 — 그 자리에 식물이 놓입니다.
    for k in (0, 1, 3):
        line(foot[k], top[k], 5)
    line(foot[3], foot[0]); line(foot[0], foot[1])
    line(top[3], top[0]);   line(top[0], top[1])
    line(foot[1], foot[2], 3); line(foot[2], foot[3], 3)
    line(rb, rf, 5)
    for t in (top[0], top[1]):
        line(t, rb)
    line(top[3], rf)

    # ── 조각 ───────────────────────────────────────────────
    dr.line([0, STRIP_Y, W, STRIP_Y], fill=GUIDE, width=3)
    for n, (pid, kind, soil_w, slots) in enumerate(PIECES):
        ox = n * CW
        dr.rectangle([ox, STRIP_Y, ox + CW - 1, H - 1], outline=GUIDE)
        if kind == "pot":
            cy = STRIP_Y + CH * POT_ANCHOR_Y
            offs = [-soil_w * .26, soil_w * .26] if slots == 2 else [0]
            rec = []
            for dx in offs:
                cx = ox + CW / 2 + dx
                rw = (soil_w * (.44 if slots == 2 else 1)) / 2
                dr.ellipse([cx - rw, cy - rw / ISO, cx + rw, cy + rw / ISO],
                           outline=MARK, width=3)
                dr.line([cx - 6, cy, cx + 6, cy], fill=MARK, width=2)
                rec.append({"x": round(cx), "y": round(cy), "w": round(rw * 2)})
            meta["pieces"].append({"id": pid, "kind": "pot", "cell": n,
                                   "box": [ox, STRIP_Y, ox + CW, H],
                                   "slots": rec})
        else:
            by = STRIP_Y + CH * PLANT_ANCHOR_Y
            cx = ox + CW / 2
            dr.line([ox + 16, by, ox + CW - 16, by], fill=MARK, width=3)
            dr.line([cx, by - 18, cx, by + 8], fill=MARK, width=3)
            half = 120 * 1.6 / 2
            for x in (cx - half, cx + half):
                dr.line([x, STRIP_Y + 12, x, by], fill=SOFT, width=2)
            meta["pieces"].append({"id": pid, "kind": "plant", "cell": n,
                                   "box": [ox, STRIP_Y, ox + CW, H],
                                   "anchor": {"x": round(cx), "y": round(by)},
                                   "maxHalfWidth": round(half)})

    im.save(out)
    json.dump(meta, open(out.replace(".png", ".json"), "w"), indent=1)
    print(f"{out}  {W}x{H}")
    print(f"  무대 {N}x{N} · 타일 {TW}x{round(TH)} · 등각 {ISO}:1")
    print(f"  조각 {len(PIECES)}개 (화분 3 · 식물 3), 칸 {CW}x{CH}")


if __name__ == "__main__":
    main()
