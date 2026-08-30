"""식물 아바타(식물 + 화분 + 그림자)를 받기 위한 기준 그림.

접합점을 생성기에 맡기지 않습니다. 화분의 흙 자리와 식물의 밑동 자리를
우리가 미리 그려 보내고 "이 표시에 정확히 맞춰 그려라" 고 시킵니다.
그러면 받은 뒤에 기준점을 찾을 필요가 없습니다 - 우리가 그린 자리가
곧 기준점입니다.

긴 화단은 흙 자리를 두 개 그립니다. 같은 식물을 두 그루 심는 자리입니다.
"""
import json
from PIL import Image, ImageDraw

W, H = 1536, 1024
COLS, ROWS = 6, 4
CW, CH = W // COLS, H // ROWS          # 256 x 256
ISO = 2.0                               # 흙 타원의 가로:세로

MARK = (232, 120, 40)
MARK_SOFT = (245, 196, 160)
GUIDE = (222, 222, 218)

# 화분 12종. long 이면 흙 자리를 두 개 그립니다.
POTS = [
    ("pot_terracotta", 120, False), ("pot_bowl", 132, False),
    ("pot_cylinder", 104, False),   ("pot_urn", 112, False),
    ("pot_white", 120, False),      ("pot_mint", 120, False),
    ("pot_charcoal", 120, False),   ("pot_rattan", 126, False),
    ("pot_concrete", 116, False),   ("bed_window", 200, True),
    ("bed_wood", 200, True),        ("bucket_metal", 100, False),
]
PLANTS = [
    "monstera", "strelitzia", "bamboo", "areca", "eucalyptus", "dieffenbachia",
    "snake", "fiddle", "zz", "pothos", "fern", "rubber",
]

POT_ANCHOR_Y = 0.40      # 셀 안에서 흙 자리의 세로 위치 (아래로 화분 몸통)
PLANT_ANCHOR_Y = 0.86    # 셀 안에서 밑동 자리 (위로 잎)


def cell_origin(n):
    r, c = divmod(n, COLS)
    return c * CW, r * CH


def main(out="sheets/avatar_ref.png"):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    meta = {"cellW": CW, "cellH": CH, "cols": COLS, "rows": ROWS,
            "iso": ISO, "pots": [], "plants": []}

    for n, (name, soil_w, long_bed) in enumerate(POTS):
        ox, oy = cell_origin(n)
        dr.rectangle([ox, oy, ox + CW - 1, oy + CH - 1], outline=GUIDE)
        cy = oy + CH * POT_ANCHOR_Y
        # 긴 화단은 흙 자리 두 개. 같은 식물을 두 그루 심습니다.
        offsets = [-soil_w * .28, soil_w * .28] if long_bed else [0]
        slots = []
        for k, dx in enumerate(offsets):
            cx = ox + CW / 2 + dx
            rw = (soil_w * (.46 if long_bed else 1)) / 2
            dr.ellipse([cx - rw, cy - rw / ISO, cx + rw, cy + rw / ISO],
                       outline=MARK, width=3)
            dr.line([cx - 5, cy, cx + 5, cy], fill=MARK, width=2)
            dr.line([cx, cy - 3, cx, cy + 3], fill=MARK, width=2)
            slots.append({"x": round(cx), "y": round(cy), "w": round(rw * 2)})
        meta["pots"].append({"id": name, "cell": n, "long": long_bed,
                             "slots": slots})

    for n, name in enumerate(PLANTS):
        idx = n + len(POTS)
        ox, oy = cell_origin(idx)
        dr.rectangle([ox, oy, ox + CW - 1, oy + CH - 1], outline=GUIDE)
        by = oy + CH * PLANT_ANCHOR_Y
        cx = ox + CW / 2
        # 밑동이 닿아야 할 선과 한가운데 표시
        dr.line([ox + 14, by, ox + CW - 14, by], fill=MARK, width=3)
        dr.line([cx, by - 16, cx, by + 8], fill=MARK, width=3)
        # 잎이 넘지 말아야 할 폭 (화분 폭의 1.6배)
        half = 120 * 1.6 / 2
        for x in (cx - half, cx + half):
            dr.line([x, oy + 10, x, by], fill=MARK_SOFT, width=2)
        meta["plants"].append({"id": name, "cell": idx,
                               "x": round(cx), "y": round(by),
                               "maxHalfWidth": round(half)})

    im.save(out)
    json.dump(meta, open(out.replace(".png", ".json"), "w"), indent=1)
    print(f"{out}  {W}x{H}")
    print(f"  칸 {COLS}x{ROWS} · 화분 {len(POTS)}(긴 화단 2) · 식물 {len(PLANTS)}")
    print(f"  기준점 {out.replace('.png', '.json')}")


if __name__ == "__main__":
    main()
