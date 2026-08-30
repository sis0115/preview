"""돌아온 그림의 실제 바닥에 격자를 맞춥니다.

생성기가 바닥을 옮기거나 키우면 우리가 보낸 좌표가 어긋납니다. 그때
그림을 되돌려보내는 대신, 바닥 마름모의 네 꼭짓점을 재서 격자를 다시
계산합니다. 기하만 맞으면 되는 문제라 다시 받을 이유가 없습니다.

칸 수는 우리가 정하는 게 아니라 그림에 이미 칠해져 있습니다. 안내 이미지에
4x4 로 그려 달라고 했으므로 4 입니다 - 5 로 나누면 우리 격자선이 칠해진
타일 한가운데를 지나가 바닥이 두 겹으로 보입니다.

    python3 tools/fit_grid.py sheets/kit.png 4
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw


def floor_mask(rgb, alpha):
    """바닥 = 채도 낮고 밝은 영역. 잔디(초록)와 유리(푸른빛)를 뺍니다."""
    a = rgb.astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (alpha > 120) & (sat < .12) & (mx > .82) & (g < r + .03) & (b < r + .03)


def corners(mask):
    """마름모의 위·오른쪽·아래·왼쪽 꼭짓점."""
    ys, xs = np.nonzero(mask)
    top = ys.min()
    bot = ys.max()
    return {
        "top": (int(np.median(xs[ys < top + 4])), int(top)),
        "bottom": (int(np.median(xs[ys > bot - 4])), int(bot)),
        "left": (int(xs.min()), int(np.median(ys[xs < xs.min() + 4]))),
        "right": (int(xs.max()), int(np.median(ys[xs > xs.max() - 4]))),
    }


def main(path, n=4, stage_h=640, out="sheets/kit_ref.json"):
    n = int(n)
    im = Image.open(path).convert("RGBA")
    stage = im.crop((0, 0, im.width, stage_h))
    rgb = np.asarray(stage.convert("RGB"))
    alpha = np.asarray(stage.getchannel("A"))
    m = floor_mask(rgb, alpha)
    # 가장 큰 덩어리만 (선반 위 흰 소품 제거)
    from scipy import ndimage  # noqa
    lab, cnt = ndimage.label(m)
    if cnt > 1:
        sizes = ndimage.sum(m, lab, range(1, cnt + 1))
        m = lab == (int(np.argmax(sizes)) + 1)

    c = corners(m)
    T, R, B, L = (np.array(c[k], float) for k in ("top", "right", "bottom", "left"))

    # 네 꼭짓점은 격자의 바깥 모서리입니다. 칸 한가운데는 거기서 반 칸
    # 안쪽이므로, 중심 좌표로 계산하면 반 칸씩 밀립니다.
    u = (R - T) / n          # i 가 1 늘 때의 이동
    v = (L - T) / n          # j 가 1 늘 때의 이동
    err = np.linalg.norm(T + n * u + n * v - B)
    print(f"바닥 꼭짓점  위{c['top']}  오{c['right']}  아{c['bottom']}  왼{c['left']}")
    print(f"평행사변형 오차 {err:.1f}px  (앞 꼭짓점이 예상과 얼마나 다른지)")

    tile_w = abs(u[0]) + abs(v[0])
    tile_h = abs(u[1]) + abs(v[1])
    print(f"바닥 {R[0]-L[0]:.0f} x {B[1]-T[1]:.0f}   등각 {(R[0]-L[0])/(B[1]-T[1]):.2f} : 1")
    print(f"→ 격자 {n}x{n} · 타일 {tile_w:.1f} x {tile_h:.1f}")

    cells = []
    for i in range(n):
        for j in range(n):
            pt = T + (i + .5) * u + (j + .5) * v
            cells.append({"i": i, "j": j, "x": round(pt[0]), "y": round(pt[1])})

    meta = json.load(open(out))
    meta["stage"].update({
        "grid": n, "tileW": round(tile_w, 1), "tileH": round(tile_h, 1),
        "originX": round(cells[0]["x"]), "originY": round(cells[0]["y"]),
        "topX": round(T[0]), "topY": round(T[1]),
        "uX": round(u[0], 3), "uY": round(u[1], 3),
        "vX": round(v[0], 3), "vY": round(v[1], 3),
        "cells": cells, "fitted": True})
    meta["iso"] = round((R[0]-L[0]) / (B[1]-T[1]), 3)
    json.dump(meta, open(out, "w"), indent=1)

    # 확인용 겹쳐 보기
    chk = stage.convert("RGB")
    dr = ImageDraw.Draw(chk)
    for i in range(n):
        for j in range(n):
            q = [T + i * u + j * v, T + (i + 1) * u + j * v,
                 T + (i + 1) * u + (j + 1) * v, T + i * u + (j + 1) * v]
            dr.polygon([tuple(x) for x in q], outline=(255, 90, 0))
    for c2 in cells:
        x, y = c2["x"], c2["y"]
        dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 90, 0))
    chk.save("sheets/kit_grid_fit.png")
    print("sheets/kit_grid_fit.png — 점이 타일 한가운데인지 보세요")


if __name__ == "__main__":
    main(*sys.argv[1:])
