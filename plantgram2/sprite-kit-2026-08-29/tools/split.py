"""색상값으로 화분과 식물을 갈라 마스크를 만듭니다.

한 장에 그려진 화분 식물이라도, 테라코타는 주황(색상 0.13 미만)이고
잎은 초록(0.16~0.55)이라 색상만으로 깨끗하게 나뉩니다. 마스크를 미리
뽑아 두면 앱에서 화분만, 또는 잎만 물들일 수 있습니다.

    python3 tools/split.py sliced/stages_a
      → sliced/stages_a/masks/s00_pot.png, s00_leaf.png ...
"""
import sys, os, json
from PIL import Image

POT_HUE = 0.13      # 이보다 작으면 테라코타·흙
LEAF_LO, LEAF_HI = 0.16, 0.55
SAT_MIN = 0.15      # 채도가 낮으면 회색 화분·유리 — 어느 쪽도 아닙니다


def hue_sat(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0, 0.0
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6, d / mx


def masks(path):
    im = Image.open(path).convert("RGBA")
    px = im.load()
    pot = Image.new("L", im.size, 0)
    leaf = Image.new("L", im.size, 0)
    pp, lp = pot.load(), leaf.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s = hue_sat(r, g, b)
            if s < SAT_MIN:
                continue
            if h < POT_HUE or h > 0.92:
                pp[x, y] = a
            elif LEAF_LO <= h <= LEAF_HI:
                lp[x, y] = a
    return im, pot, leaf


def main(d):
    out = os.path.join(d, "masks")
    os.makedirs(out, exist_ok=True)
    rows = []
    for f in sorted(x for x in os.listdir(d) if x.endswith(".png")):
        stem = f[:-4]
        im, pot, leaf = masks(os.path.join(d, f))
        pot.save(os.path.join(out, f"{stem}_pot.png"))
        leaf.save(os.path.join(out, f"{stem}_leaf.png"))
        tot = sum(1 for v in im.getchannel("A").get_flattened_data() if v)
        np = sum(1 for v in pot.get_flattened_data() if v)
        nl = sum(1 for v in leaf.get_flattened_data() if v)
        rows.append((stem, np, nl, tot))
    w = max(len(r[0]) for r in rows)
    print(f"{'':{w}}  {'화분':>8} {'잎':>8} {'분류율':>7}")
    for stem, np, nl, tot in rows:
        pct = (np + nl) / tot * 100 if tot else 0
        flag = "" if pct > 80 else "   ← 낮음, 무채색 화분일 수 있습니다"
        print(f"{stem:{w}}  {np:8d} {nl:8d} {pct:6.1f}%{flag}")
    json.dump(
        [{"id": s, "potPx": p, "leafPx": l} for s, p, l, _ in rows],
        open(os.path.join(out, "index.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
