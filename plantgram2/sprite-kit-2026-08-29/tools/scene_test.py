"""조각을 배경 위에 실제로 놓아 봅니다.

기하는 셋에서 옵니다.
  · 격자   stage_grid.json  (배경의 앞변에서 읽은 값)
  · 기준점 조각 시트에서 잰 흙 자리와 줄기 밑동
  · 배율   조각 전체에 곱하는 한 값. 조각 하나만 늘리지 않습니다.

    python3 tools/scene_test.py
"""
import colorsys, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

sys.path.insert(0, "tools")
from verify_spec import alpha_of, components, stem_of, foot_of   # noqa: E402
from compose_test import soils, cut                              # noqa: E402

# 표준 화분이 타일의 몇 할을 차지할지. 이 한 값으로 모든 조각을 줄입니다.
POT_ON_TILE = .80


def load(sheet="sheets/spec_04_art.png", spec_path="sheets/spec_04.json"):
    spec = json.load(open(spec_path))
    im = Image.open(sheet).convert("RGBA")
    mask = alpha_of(im)
    out = {}
    for it, (g, own) in zip(spec["items"], components(mask)):
        art = cut(im, own, g)
        if it["kind"] == "식물":
            x, y = stem_of(own, g)
            out[it["id"]] = dict(art=art, kind="식물",
                                 anchor=[(x - g[0], y - g[1])])
        else:
            want = 2 if it["id"] == "bed_long" else 1
            fx, fy = foot_of(own, g)
            out[it["id"]] = dict(
                art=art, kind=it["kind"], foot=(fx - g[0], fy - g[1]),
                anchor=[(x - g[0], y - g[1])
                        for x, y in soils(im, own, g, want)] if it["kind"] == "화분" else [])
    return out


def shadow(width, iso, shape="ellipse", ink=104, blur=.34):
    """접지 그림자. 바닥에 놓인 자국이므로 높이는 폭 ÷ 등각비입니다.

    둥근 화분은 타원이지만, 다리 달린 선반이나 상자꼴 화단은 밑면이
    마름모입니다. 타원을 깔면 다리 사이가 비어 떠 보입니다.
    """
    w = max(8, round(width))
    h = max(4, round(w / iso))
    pad = round(w * .3)
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    tone = (58, 48, 36, ink)
    if shape == "diamond":
        cx, cy = pad + w / 2, pad + h / 2
        dr.polygon([(cx, pad), (pad + w, cy), (cx, pad + h), (pad, cy)], fill=tone)
    else:
        dr.ellipse([pad, pad, pad + w, pad + h], fill=tone)
    return im.filter(ImageFilter.GaussianBlur(pad * blur))


def main(out="sheets/scene_test.png"):
    grid = json.load(open("sheets/stage_grid.json"))
    T = np.array([grid["topX"], grid["topY"]])
    u = np.array([grid["uX"], grid["uY"]])
    v = np.array([grid["vX"], grid["vY"]])
    iso = grid["tileW"] / grid["tileH"]

    piece = load()
    unit = grid["tileW"] * POT_ON_TILE / piece["pot_round"]["art"].width
    print(f"조각 배율 {unit:.4f}  (표준 화분 {piece['pot_round']['art'].width}px "
          f"→ 타일 {grid['tileW']}의 {POT_ON_TILE:.0%})")

    stage = Image.open("sheets/stage.png").convert("RGBA")

    # (칸 i, 칸 j, 화분, 식물)
    plan = [
        (0, 2, "planter_big", "plant_big"),   # 뒤 가운데 — 특대형
        (2, 0, "shelf", None),                # 오른쪽 뒤
        (1, 4, "pot_round", "plant_m"),       # 왼쪽
        (4, 2, "bed_long", "plant_s"),        # 오른쪽 앞 — 두 그루
        (3, 4, "pot_round", "plant_tall"),    # 왼쪽 앞
    ]

    def centre(i, j):
        return T + u * (i + .5) + v * (j + .5)

    # 화면에서 아래에 있는 것이 앞입니다.
    plan.sort(key=lambda p: centre(p[0], p[1])[1])

    for i, j, pot_id, plant_id in plan:
        at = centre(i, j)
        pot = piece[pot_id]
        s = unit
        pw, ph = pot["art"].size
        art = pot["art"].resize((round(pw * s), round(ph * s)), Image.LANCZOS)
        fx, fy = pot["foot"][0] * s, pot["foot"][1] * s

        sh = shadow(art.width * .80, iso)
        stage.alpha_composite(sh, (round(at[0] - sh.width / 2),
                                   round(at[1] - sh.height / 2)))
        stage.alpha_composite(art, (round(at[0] - fx), round(at[1] - fy)))

        if plant_id is None:
            continue
        pl = piece[plant_id]
        plw, plh = pl["art"].size
        leaf = pl["art"].resize((round(plw * s), round(plh * s)), Image.LANCZOS)
        sx, sy = pl["anchor"][0][0] * s, pl["anchor"][0][1] * s
        for ax, ay in sorted(pot["anchor"], key=lambda p: p[1]):
            px = at[0] - fx + ax * s - sx
            py = at[1] - fy + ay * s - sy
            stage.alpha_composite(leaf, (round(px), round(py)))

    stage.convert("RGB").save(out)
    print(f"{out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
