"""찾은 점으로 실제 조합해서 확대해 봅니다. 이게 진짜 시험입니다.

숫자가 맞는 것과 눈에 맞아 보이는 것은 다릅니다. 화분의 흙 자리와 식물의
줄기 밑동을 겹쳐 놓고 4배로 확대해서, 줄기가 흙 한가운데에 박혔는지 봅니다.

    python3 tools/compose_test.py sheets/spec_04_art.png sheets/spec_04.json
"""
import colorsys
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, "tools")
from verify_spec import alpha_of, components, stem_of, foot_of   # noqa: E402

FONT = "../app-kit/assets/fonts/{}.otf"


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def soils(im, mask, box, want):
    """심는 자리들. 갈색 덩어리를 찾아 넓은 것부터 [want] 개 고릅니다.

    긴 화단은 흙이 두 곳으로 나뉘어 있으므로 덩어리도 둘입니다.
    """
    x0, y0, x1, y1 = box
    rgb = np.asarray(im.convert("RGB")).astype(float)[y0:y1 + 1, x0:x1 + 1] / 255
    sub = mask[y0:y1 + 1, x0:x1 + 1]
    h, w, _ = rgb.shape
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in rgb.reshape(-1, 3)])
    hue, sat, val = (hsv[:, i].reshape(h, w) for i in range(3))
    soil = sub & ((hue < .13) | (hue > .92)) & (sat > .18) & (val < .62)
    lab, k = ndimage.label(ndimage.binary_opening(soil, np.ones((3, 3))))
    parts = []
    for c in range(1, k + 1):
        ys, xs = np.nonzero(lab == c)
        if len(xs) < 300:
            continue
        parts.append((len(xs), x0 + xs.mean(), y0 + ys.mean()))
    parts.sort(reverse=True)
    if len(parts) < want:                      # 한 덩어리로 보이면 좌우로 가릅니다
        ys, xs = np.nonzero(soil)
        edges = np.linspace(xs.min(), xs.max() + 1, want + 1)
        parts = []
        for a, b in zip(edges, edges[1:]):
            sel = (xs >= a) & (xs < b)
            parts.append((sel.sum(), x0 + xs[sel].mean(), y0 + ys[sel].mean()))
    return sorted([(p[1], p[2]) for p in parts[:want]])


def cut(im, own, box):
    """자기 덩어리만 오립니다. 네모로만 오리면 옆 물체가 딸려 옵니다."""
    x0, y0, x1, y1 = box
    art = im.crop((x0, y0, x1 + 1, y1 + 1)).copy()
    a = np.asarray(art.getchannel("A"))
    art.putalpha(Image.fromarray((a * own[y0:y1 + 1, x0:x1 + 1]).astype("uint8")))
    return art


def main(art_path, spec_path="sheets/spec_04.json",
         out="sheets/spec_04_compose.png"):
    spec = json.load(open(spec_path))
    im = Image.open(art_path).convert("RGBA")
    mask = alpha_of(im)
    got = components(mask)

    piece, anchor = {}, {}
    for it, (g, own) in zip(spec["items"], got):
        piece[it["id"]] = (cut(im, own, g), g)
        if it["kind"] == "식물":
            x, y = stem_of(own, g)
            anchor[it["id"]] = [(x - g[0], y - g[1])]
        else:
            want = 2 if it["id"] == "bed_long" else 1
            anchor[it["id"]] = [(x - g[0], y - g[1])
                                for x, y in soils(im, own, g, want)]

    combos = [
        ("pot_round", "plant_m", "둥근 화분 + 식물"),
        ("pot_round", "plant_s", "둥근 화분 + 작은 식물"),
        ("bed_long", "plant_s", "긴 화단 + 작은 식물 두 그루"),
        ("bed_long", "plant_m", "긴 화단 + 식물 두 그루"),
        ("planter_big", "plant_big", "큰 화분 + 특대형 식물"),
        ("planter_big", "plant_tall", "큰 화분 + 키 큰 식물"),
    ]

    made = []
    for pot_id, plant_id, label in combos:
        pot, _ = piece[pot_id]
        plant, _ = piece[plant_id]
        sx, sy = anchor[plant_id][0]
        spots = anchor[pot_id]

        # 화분과 식물을 모두 담을 상자를 먼저 잽니다.
        boxes = [(0, 0, pot.width, pot.height)]
        for ax, ay in spots:
            boxes.append((ax - sx, ay - sy,
                          ax - sx + plant.width, ay - sy + plant.height))
        l = min(b[0] for b in boxes)
        t = min(b[1] for b in boxes)
        r = max(b[2] for b in boxes)
        b = max(b[3] for b in boxes)

        canvas = Image.new("RGBA", (round(r - l), round(b - t)), (0, 0, 0, 0))
        canvas.alpha_composite(pot, (round(-l), round(-t)))
        # 뒤쪽 자리부터 심어야 앞 그루가 뒤 그루를 가립니다.
        for ax, ay in sorted(spots, key=lambda p: p[1]):
            canvas.alpha_composite(plant, (round(ax - sx - l), round(ay - sy - t)))
        marks = [(ax - l, ay - t) for ax, ay in spots]
        made.append((label, canvas, marks))

    # 두 줄로 붙입니다. 위는 조합 결과, 아래는 접합부를 4배로.
    pad = 34
    cw = max(c.width for _, c, _ in made) + pad
    ch = max(c.height for _, c, _ in made) + 84
    zoom_w = cw - pad
    zoom_h = round(zoom_w * 120 / 200)
    sheet = Image.new("RGB", (cw * len(made), ch + zoom_h + 70), (246, 246, 242))
    dr = ImageDraw.Draw(sheet)
    dr.text((16, 14), "조합 결과 — 아래는 줄기와 흙이 만나는 곳을 4배로",
            font=font(20, True), fill=(46, 64, 52))

    for n, (label, canvas, marks) in enumerate(made):
        ox = n * cw
        dr.text((ox + cw / 2, 62), label, font=font(14, True),
                fill=(70, 90, 76), anchor="ms")
        px = round(ox + (cw - canvas.width) / 2)
        py = round(76 + (ch - 84 - canvas.height))
        sheet.paste(canvas, (px, py), canvas)

        mx, my = marks[0]
        crop = canvas.crop((round(mx - 100), round(my - 70),
                            round(mx + 100), round(my + 50)))
        flat = Image.new("RGB", crop.size, (255, 255, 255))
        flat.paste(crop, (0, 0), crop)
        sheet.paste(flat.resize((zoom_w, zoom_h), Image.LANCZOS),
                    (ox + pad // 2, ch + 34))
        # 찾은 심는 자리를 확대본에도 표시합니다.
        k = zoom_w / 200
        cx = ox + pad // 2 + 100 * k
        cy = ch + 34 + 70 * k
        dr.line([(cx - 10, cy), (cx + 10, cy)], fill=(230, 90, 30), width=2)
        dr.line([(cx, cy - 10), (cx, cy + 10)], fill=(230, 90, 30), width=2)

    sheet.save(out)
    print(f"{out}")
    for (pot_id, plant_id, label), (_, c, m) in zip(combos, made):
        print(f"  {label:24} 상자 {c.width}x{c.height} · 심는 자리 {len(m)}곳")


if __name__ == "__main__":
    main(*sys.argv[1:])
