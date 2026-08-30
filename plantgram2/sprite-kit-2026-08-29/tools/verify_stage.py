"""돌아온 배경의 바닥이 우리 격자와 맞는지 봅니다.

맞으면 우리 좌표를 그대로 씁니다 - 다시 재서 격자를 되짚지 않습니다.
어긋나면 다시 받습니다. 흡수하지 않습니다.

    python3 tools/verify_stage.py sheets/stage.png sheets/stage_guide.json
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw


def floor_mask(rgb):
    """바닥 = 채도 낮고 밝은 영역. 잔디(초록)와 유리(푸른빛)를 뺍니다."""
    a = rgb.astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (sat < .14) & (mx > .78) & (g < r + .04) & (b < r + .05)


def corners(mask):
    ys, xs = np.nonzero(mask)
    top, bot = ys.min(), ys.max()
    return {
        "top": (int(np.median(xs[ys < top + 5])), int(top)),
        "bottom": (int(np.median(xs[ys > bot - 5])), int(bot)),
        "left": (int(xs.min()), int(np.median(ys[xs < xs.min() + 5]))),
        "right": (int(xs.max()), int(np.median(ys[xs > xs.max() - 5]))),
    }


def main(art, spec_path="sheets/stage_guide.json", out=None):
    out = out or "sheets/stage_check.png"
    spec = json.load(open(spec_path))
    im = Image.open(art).convert("RGB")
    if im.size != (spec["width"], spec["height"]):
        print(f"크기가 다릅니다: {im.size} — 다시 받아야 합니다")
        return 1

    rgb = np.asarray(im)
    m = floor_mask(rgb)
    # 바닥이 있어야 할 자리 안쪽만 봅니다 (밖의 흰 하늘 등을 빼려고)
    h, w = m.shape
    yy, xx = np.mgrid[0:h, 0:w]
    c = spec["corners"]
    hw = (c["right"][0] - c["left"][0]) / 2 + 40
    hh = (c["bottom"][1] - c["top"][1]) / 2 + 40
    inside = (np.abs(xx - spec["originX"]) / hw
              + np.abs(yy - spec["originY"]) / hh) <= 1
    got = corners(m & inside)

    dr = ImageDraw.Draw(im)
    bad = 0
    print(f"{'꼭짓점':6} {'우리가 정한 자리':>18} {'그려진 자리':>14}   차이")
    for k in ("top", "right", "bottom", "left"):
        want = tuple(c[k])
        have = got[k]
        d = ((have[0] - want[0]) ** 2 + (have[1] - want[1]) ** 2) ** .5
        ok = d <= 16
        bad += 0 if ok else 1
        print(f"{k:6} {str(want):>18} {str(have):>14}   {d:5.1f}px"
              + ("   맞음" if ok else "   ← 어긋남"))
        dr.ellipse([want[0] - 9, want[1] - 9, want[0] + 9, want[1] + 9],
                   outline=(40, 150, 80) if ok else (205, 70, 45), width=3)
        dr.ellipse([have[0] - 5, have[1] - 5, have[0] + 5, have[1] + 5],
                   outline=(30, 80, 200), width=3)

    # 우리 격자를 얹어 봅니다. 이음선과 겹치는지 눈으로 봅니다.
    for cellrec in spec["cells"]:
        x, y = cellrec["x"], cellrec["y"]
        hwt, hht = spec["tileW"] / 2, spec["tileH"] / 2
        dr.polygon([(x, y - hht), (x + hwt, y), (x, y + hht), (x - hwt, y)],
                   outline=(232, 106, 30))
    im.save(out)
    print(f"\n{out} — 초록/빨강 = 우리가 정한 꼭짓점, 파랑 = 그려진 꼭짓점,"
          " 주황 = 우리 격자")
    print("주황 선이 칠해진 이음선과 겹치는지 확대해서 보세요.")
    if bad:
        print("\n꼭짓점이 어긋났습니다. 코드로 맞추지 말고 다시 받으세요.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
