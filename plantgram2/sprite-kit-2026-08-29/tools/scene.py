"""정원 장면을 그립니다 — 타일을 등각 격자에 깔고 그 위에 화분 식물을 얹습니다.

타일과 화분이 서로 다른 각도로 그려져 왔습니다. 화분의 흙 타원은 2.82:1,
타일 윗면 마름모는 1.56:1 입니다. 화분·식물이 훨씬 많으므로 타일을
세로로 눌러 화분 쪽에 맞춥니다.
"""
import os, sys
import numpy as np
from PIL import Image

ISO = 2.82          # 화분에서 실측한 윗면 비율 (폭 ÷ 높이)
TILE_W = 156        # 화면에 그릴 타일 폭


def top_face(im):
    """윗면 마름모의 폭과 높이, 그리고 옆면 두께"""
    a = np.array(im.getchannel("A")) > 40
    ys, xs = np.nonzero(a)
    x0, x1 = xs.min(), xs.max()
    vy = (ys[xs == x0].min() + ys[xs == x1].min()) / 2
    return x1 - x0, (vy - ys.min()) * 2, ys.max() - vy


def fit_tile(im, width=TILE_W, iso=ISO):
    """윗면 비율이 iso 가 되도록 세로로 누르고, 지정 폭으로 맞춥니다"""
    w, h, _ = top_face(im)
    k = (w / iso) / h                      # 세로 눌림 비율
    sx = width / w
    return im.resize((max(1, round(im.width * sx)),
                      max(1, round(im.height * k * sx))), Image.LANCZOS)


def anchor_bottom(im):
    """타일 윗면의 한가운데 — 이 자리에 물건을 세웁니다"""
    w, h, thick = top_face(im)
    a = np.array(im.getchannel("A")) > 40
    ys, xs = np.nonzero(a)
    return (xs.min() + xs.max()) // 2, round(ys.min() + h)


def render(plan, tiledir, combodir, out, pad=80, tile_w=TILE_W):
    """plan: {(i, j): 타일이름} 과 {(i, j): 조합이름} 두 벌"""
    tiles, items = plan["tiles"], plan.get("items", {})
    raw = {n: Image.open(f"{tiledir}/{n}.png").convert("RGBA") for n in set(tiles.values())}
    cache = {n: fit_tile(im, tile_w) for n, im in raw.items()}
    # 타일을 줄인 만큼 화분 식물도 같이 줄입니다. 시트가 한 축척으로
    # 그려져 있으므로 배율 하나면 충분합니다 - 타일만 줄이면 식물이
    # 타일보다 커집니다.
    k = tile_w / top_face(next(iter(raw.values())))[0]
    tw = tile_w
    th = round(tw / ISO)
    cells = sorted(tiles, key=lambda c: c[0] + c[1])
    xs = [(i - j) * tw // 2 for i, j in cells]
    ys = [(i + j) * th // 2 for i, j in cells]
    W = max(xs) - min(xs) + tw + pad * 2
    H = max(ys) - min(ys) + th * 3 + pad * 2
    ox, oy = pad - min(xs), pad + th * 2 - min(ys)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, j in cells:
        t = cache[tiles[(i, j)]]
        ax, ay = anchor_bottom(t)
        cx = ox + (i - j) * tw // 2
        cy = oy + (i + j) * th // 2
        canvas.alpha_composite(t, (cx - ax, cy - ay))
        name = items.get((i, j))
        if name:
            it = Image.open(f"{combodir}/{name}.png").convert("RGBA")
            it = it.resize((max(1, round(it.width * k)), max(1, round(it.height * k))),
                           Image.LANCZOS)
            a = np.array(it.getchannel("A")) > 40
            iy, ix = np.nonzero(a)
            # 물건은 밑변 한가운데를 타일 중심에 세웁니다
            canvas.alpha_composite(
                it, (cx - (ix.min() + ix.max()) // 2, cy - iy.max()))
    canvas.save(out)
    print(f"{out}  {canvas.width}x{canvas.height}  타일 {len(cells)}칸")
