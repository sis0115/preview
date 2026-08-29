"""빈 화분 위에 화분 없는 식물을 얹습니다.

화분에서 흙 윗면을, 식물에서 밑동을 찾아 두 자리를 맞춥니다.
종별로 성체(s4) 기준 배율을 하나 정하고 모든 단계에 같은 배율을 쓰므로,
단계가 커질수록 실제로 자라 보입니다.
"""
import os, sys, json
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from split import hue_sat

SOIL_V_MAX = 0.55        # 흙은 어둡습니다. 이보다 밝으면 화분 몸통입니다


def soil_anchor(pot):
    """식물을 심을 자리 — 흙 윗면의 무게중심.

    외접 사각형의 한가운데를 쓰면 안 됩니다. 등각으로 그린 긴 텃밭은
    흙 윗면이 평행사변형이라, 외접 사각형 중심이 실제 심는 자리에서
    한참 벗어납니다. 무게중심은 평행사변형에서도 눈에 보이는 한가운데에
    떨어집니다."""
    px = pot.load()
    xs, ys = [], []
    for y in range(pot.height):
        for x in range(pot.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s = hue_sat(r, g, b)
            v = max(r, g, b) / 255
            if v < SOIL_V_MAX and s > 0.2 and (h < 0.13 or h > 0.92):
                xs.append(x); ys.append(y)
    if not xs:
        return pot.width // 2, int(pot.height * 0.3)
    return round(sum(xs) / len(xs)), round(sum(ys) / len(ys))


def stem_anchor(plant, rows=10):
    """밑동이 절단선에 닿는 자리"""
    a = plant.load()
    xs = [x for y in range(max(0, plant.height - rows), plant.height)
            for x in range(plant.width) if a[x, y][3] > 0]
    if not xs:
        return plant.width // 2, plant.height
    return (min(xs) + max(xs)) // 2, plant.height


def compose(pot, plant, scale=1.0, pad=24):
    if scale != 1.0:
        plant = plant.resize((max(1, int(plant.width * scale)),
                              max(1, int(plant.height * scale))), Image.LANCZOS)
    sx, sy = soil_anchor(pot)
    tx, ty = stem_anchor(plant)
    ox, oy = sx - tx, sy - ty
    x0, y0 = min(0, ox), min(0, oy)
    W = max(pot.width, ox + plant.width) - x0 + pad * 2
    H = max(pot.height, oy + plant.height) - y0 + pad * 2
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 화분을 먼저, 식물을 위에. 반대로 하면 줄기가 흙 위로 올라오지 못하고
    # 잎만 화분 뒤에 떠 있습니다.
    out.alpha_composite(pot,   (0 - x0 + pad, 0 - y0 + pad))
    out.alpha_composite(plant, (ox - x0 + pad, oy - y0 + pad))
    return out


def species_scale(pot, mature_plant):
    """배율 없음 — 시트가 이미 같은 축척으로 그려져 있습니다.

    규격 1단위가 실측 1.88~2.33 픽셀로 ±11% 안에 들어옵니다. 여기서
    화분 폭에 맞춰 다시 키우면, 가로로 긴 텃밭에 얹을 때 식물이
    텃밭 길이만큼 부풀어 버립니다. 원본 크기 그대로가 맞습니다."""
    return 1.0


if __name__ == "__main__":
    potdir, plantdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    pots = sorted(f for f in os.listdir(potdir) if f.endswith(".png"))
    plants = sorted(f for f in os.listdir(plantdir) if f.endswith(".png"))
    n = 0
    for pf in pots:
        pot = Image.open(os.path.join(potdir, pf)).convert("RGBA")
        by_sp = {}
        for qf in plants:
            by_sp.setdefault(qf.rsplit("_", 1)[0], []).append(qf)
        for sp, files in by_sp.items():
            mature = Image.open(os.path.join(plantdir, sorted(files)[-1])).convert("RGBA")
            k = species_scale(pot, mature)
            for qf in files:
                pl = Image.open(os.path.join(plantdir, qf)).convert("RGBA")
                compose(pot, pl, k).save(
                    os.path.join(out, f"{qf[:-4]}__{pf[:-4]}.png"))
                n += 1
    print(f"{n} 조합 — {out}")
