"""돌아온 그림이 안내선을 지켰는지 검사합니다. 재지 않고, 확인만 합니다.

어긋난 그림을 코드로 흡수하지 않습니다. 통과하지 못하면 다시 받습니다 -
지금까지 흡수해 온 것이 뒤틀림과 잘림의 뿌리였습니다.

    python3 tools/verify_spec.py sheets/spec_02_art.png sheets/spec_02.json
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

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


def blobs(mask, least=3000):
    """물체 하나하나의 바깥 상자. 칸으로 자르지 않습니다 -
    칸 경계를 넘었는지도 봐야 하기 때문입니다."""
    lab, k = ndimage.label(ndimage.binary_closing(mask, np.ones((9, 9))))
    out = []
    for c in range(1, k + 1):
        ys, xs = np.nonzero(lab == c)
        if len(xs) < least:
            continue
        out.append((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    out.sort(key=lambda o: (o[1] // 400, o[0]))
    return out


def expected(it, spec):
    """안내선이 정한 가로 한가운데 · 너비 · 바닥.

    화분과 가구는 밑면이 타일을 덮으므로 마름모의 아래 꼭짓점이 바닥입니다.
    식물은 줄기만 닿으므로 십자(기준점)가 바닥입니다 - 둘을 같은 자로 재면
    식물이 늘 40px 떠 있는 것처럼 나옵니다.
    """
    hh = spec["tileH"] / 2
    xs = [x for x, _ in it["tiles"]]
    ys = [y for _, y in it["tiles"]]
    bottom = it["ground"][1] if it["kind"] == "식물" else max(ys) + hh
    width = it.get("allowW", (max(xs) - min(xs)) + spec["tileW"])
    return it["ground"][0], width, bottom


def main(art, spec_path="sheets/spec_02.json", out=None):
    out = out or spec_path.replace(".json", "_check.png")
    spec = json.load(open(spec_path))
    im = Image.open(art).convert("RGBA")
    if im.size != (spec["width"], spec["height"]):
        print(f"크기가 다릅니다: {im.size} ≠ "
              f"({spec['width']}, {spec['height']}) — 다시 받아야 합니다")
        return 1

    mask = alpha_of(im)
    got = blobs(mask)
    if len(got) != len(spec["items"]):
        print(f"물체가 {len(got)}개입니다 (있어야 할 수 {len(spec['items'])}) — "
              "겹쳤거나 빠졌습니다")

    guide = Image.open(spec_path.replace(".json", ".png")).convert("RGB")
    chk = Image.alpha_composite(guide.convert("RGBA"), im).convert("RGB")
    dr = ImageDraw.Draw(chk)
    bad = 0

    print(f"{'칸':2} {'이름':12} {'가로중심':>8} {'바닥':>6} "
          f"{'너비':>6} {'맞을너비':>8} {'배':>5}   판정")
    for it, g in zip(spec["items"], got):
        exc, exw, exb = expected(it, spec)
        w = g[2] - g[0]
        dc = (g[0] + g[2]) / 2 - exc
        db = g[3] - exb
        ok = abs(dc) <= TOL and abs(db) <= TOL and abs(w / exw - 1) <= .12
        bad += 0 if ok else 1
        color = (40, 150, 80) if ok else (205, 70, 45)
        dr.rectangle([exc - exw / 2, exb - 7, exc + exw / 2, exb],
                     outline=color, width=3)
        dr.rectangle(g, outline=(30, 80, 200), width=2)
        print(f"{it['cell'] + 1:2} {it['id']:12} {dc:+8.0f} {db:+6.0f} "
              f"{w:6} {exw:8.0f} {w / exw:5.2f}"
              + ("   통과" if ok else "   ← 어긋남"))

    chk.save(out)
    print(f"\n{out} — 초록/빨강 = 안내선이 정한 좌·우·아래, 파랑 = 실제로 그려진 범위")
    print(f"허용: 자리 {TOL}px · 너비 ±12%. 키는 검사하지 않습니다.")
    print(f"{len(spec['items']) - bad}/{len(spec['items'])} 통과")
    if bad:
        print("\n어긋난 칸이 있습니다. 코드로 맞추지 말고 다시 받으세요.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
