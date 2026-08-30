"""돌아온 그림이 안내선을 지켰는지 검사합니다. 재지 않고, 확인만 합니다.

어긋난 그림을 코드로 흡수하지 않습니다. 통과하지 못하면 다시 받습니다 -
지금까지 흡수해 온 것이 뒤틀림과 잘림의 뿌리였습니다.

    python3 tools/verify_spec.py sheets/spec_01_art.png
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw

TOL = 14          # px. 이만큼까지는 봐 줍니다
KEY = (255, 0, 255)


def alpha_of(im):
    """투명이면 알파를, 마젠타 배경이면 그 반대를 씁니다."""
    a = np.asarray(im.getchannel("A"))
    if a.min() < 200:
        return a > 110
    rgb = np.asarray(im.convert("RGB")).astype(int)
    d = np.abs(rgb - np.array(KEY)).sum(2)
    return d > 120


def bbox(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def expected(it, spec):
    """안내선이 정한 물체의 바깥 상자."""
    tiles = it["tiles"]
    hw, hh = spec["tileW"] / 2, spec["tileH"] / 2
    xs = [x for x, _ in tiles]
    ys = [y for _, y in tiles]
    top = min(ys) - hh - spec["unit"] * it["height"]
    return (min(xs) - hw, top, max(xs) + hw, max(ys) + hh)


def main(art, spec_path="sheets/spec_01.json", out="sheets/spec_01_check.png"):
    spec = json.load(open(spec_path))
    im = Image.open(art).convert("RGBA")
    if im.size != (spec["width"], spec["height"]):
        print(f"크기가 다릅니다: {im.size} ≠ "
              f"({spec['width']}, {spec['height']}) — 다시 받아야 합니다")
        return 1

    mask = alpha_of(im)
    chk = im.convert("RGB")
    dr = ImageDraw.Draw(chk)
    bad = 0

    print(f"{'칸':2} {'이름':12} {'좌':>6} {'우':>6} {'위':>6} {'아래':>6}   판정")
    for it in spec["items"]:
        x0, y0, x1, y1 = it["box"]
        got = bbox(mask[y0:y1, x0:x1])
        ex = expected(it, spec)
        if got is None:
            print(f"{it['cell'] + 1:2} {it['id']:12} {'—':>6}{'':21}   빈 칸")
            bad += 1
            continue
        g = (got[0] + x0, got[1] + y0, got[2] + x0, got[3] + y0)
        d = [g[0] - ex[0], g[2] - ex[2], g[1] - ex[1], g[3] - ex[3]]
        ok = all(abs(v) <= TOL for v in d)
        bad += 0 if ok else 1
        dr.rectangle(ex, outline=(60, 160, 90) if ok else (200, 70, 50), width=3)
        dr.rectangle(g, outline=(40, 90, 200), width=1)
        print(f"{it['cell'] + 1:2} {it['id']:12} "
              + " ".join(f"{v:+6.0f}" for v in d)
              + ("   통과" if ok else "   ← 어긋남"))

    chk.save(out)
    print(f"\n{out} — 초록/빨강 = 안내선이 정한 상자, 파랑 = 실제 그려진 범위")
    print(f"허용 오차 {TOL}px · {len(spec['items']) - bad}/{len(spec['items'])} 통과")
    if bad:
        print("\n어긋난 칸이 있습니다. 코드로 맞추지 말고 다시 받으세요.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
