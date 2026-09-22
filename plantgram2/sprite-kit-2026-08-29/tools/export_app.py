"""앱이 쓸 에셋과 카탈로그를 내보냅니다.

세 곳에서 모읍니다.
  · 등급 시트   화분 5 · 긴 화단 · 식물 5
  · 4차 시트    선반 · 시멘트 큰 화분 (등급 시트에 없는 것)
  · 배경        무대 그림과 앞변에서 읽은 격자

축척은 한 값으로 통일합니다. 등급 시트는 긴 화단으로 4차 시트에 맞추고,
그 다음 무대 타일에 맞춥니다. 조각 하나만 늘리지 않습니다.

    python3 tools/export_app.py ../app-kit/assets
"""
import json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, "tools")
from grade_kit import load as load_grade, scaled     # noqa: E402
from scene_test import load as load_kit, shadow      # noqa: E402
from furniture_kit import load as load_furniture, KEEP as FURNITURE  # noqa: E402

SHEET_TILE = 225.0

NAMES = {
    "pot_sprout": "새싹 화분", "pot_small": "소형 화분",
    "pot_medium": "중형 화분", "pot_large": "대형 화분",
    "pot_xlarge": "특대형 화분", "bed_long": "긴 화단",
    "shelf": "선반", "planter_big": "석재 화분",
    "shelf_planted": "심어 놓은 선반", "bench_planted": "모종 작업대",
    "sprout": "새싹", "small": "소형", "medium": "중형",
    "large": "대형", "xlarge": "특대형",
}
BOXY = {"bed_long", "shelf", "planter_big", "shelf_planted",
        "bench_planted"}

# 등급마다 어울리는 화분. 심을 때 이 화분에 담깁니다.
DEFAULT_POT = {"sprout": "pot_sprout", "small": "pot_small",
               "medium": "pot_medium", "large": "pot_large",
               "xlarge": "pot_xlarge"}

# 자리마다 **어느 등급이 들어가는지**. 크기가 안 맞으면 줄이는 게 아니라
# 놓을 수 없다고 알려 줍니다(RULES 8). 선반은 자리가 아직 없어 가구입니다 -
# 가구 시트가 오면 여기에 자리가 붙습니다.
SLOT_GRADE = {
    "pot_sprout": ["sprout"], "pot_small": ["small"],
    "pot_medium": ["medium"], "pot_large": ["large"],
    "pot_xlarge": ["xlarge"],
    "bed_long": ["small", "small"],     # 두 칸짜리 식물 하나가 아니라 두 그루
    "planter_big": ["xlarge"],
    # 자리가 없으면 가구입니다. 선반은 빈 그림을 아직 못 받았고, 아래 둘은
    # 화분과 식물이 그려져 들어와 장식으로만 씁니다.
    "shelf": [], "shelf_planted": [], "bench_planted": [],
}


def footprint(stage_w, tile_w):
    """조각이 몇 칸을 차지하는지. **재서 나오는 값이지 정하는 값이 아닙니다.**

    한 칸 마름모의 가로가 타일 폭입니다. 그보다 넓은 조각을 한 칸에 놓으면
    옆 칸을 침범해, 그 칸에 다른 것을 놓을 수 없는데도 비어 보입니다.

    긴 조각의 긴 축은 그림에서 오른쪽 위로 뻗습니다(-v 방향). 그래서 넓은
    것은 j 를 하나 더 먹는 1 x 2 가 됩니다. 2 x 2 가 필요한 조각은 아직
    없습니다 - 가장 넓은 석재 화분도 1 x 2 안에 들어갑니다.
    """
    return [1, 2] if stage_w > tile_w else [1, 1]


def slot_grades(pid, n):
    """자리 수와 등급표의 길이가 어긋나도 그림이 정한 자리 수를 따릅니다."""
    g = SLOT_GRADE.get(pid) or ["medium"]
    return [g[min(k, len(g) - 1)] for k in range(n)]


def main(out="../app-kit/assets"):
    grid = json.load(open("sheets/stage_grid.json"))
    to_stage = grid["tileW"] / SHEET_TILE
    iso = grid["tileW"] / grid["tileH"]

    grade, unit = load_grade()
    kit = load_kit()

    pieces = {}
    for k, v in grade.items():
        pieces[k] = scaled(v, unit)              # 4차 시트 좌표계로
    for k in ("shelf", "planter_big"):
        pieces[k] = kit[k]
    # 가구 시트. 알파가 들어 있어 지울 배경이 없고, 긴 화단으로 축척을
    # 맞춥니다 - 조각 하나만 늘리지 않습니다.
    furn, f_unit = load_furniture(bed_width=pieces["bed_long"]["art"].width)
    for k in FURNITURE:
        pieces[k] = furn[k]
    print(f"가구 시트 축척 {f_unit:.4f} · {', '.join(FURNITURE)}")

    for d in ("greenhouse", "pots", "plants", "shadows"):
        os.makedirs(f"{out}/{d}", exist_ok=True)
    Image.open("sheets/stage.png").convert("RGBA").save(f"{out}/greenhouse/stage.png")

    cat = {"pots": {}, "plants": {}, "grid": {
        "n": grid["n"], "tileW": grid["tileW"], "tileH": grid["tileH"],
        "topX": grid["topX"], "topY": grid["topY"],
        "uX": grid["uX"], "uY": grid["uY"],
        "vX": grid["vX"], "vY": grid["vY"],
        "sceneW": grid["sceneW"], "sceneH": grid["sceneH"],
        "unitScale": round(to_stage, 4)}}

    print(f"{'조각':14} {'폭':>5} {'높이':>5}  기준점")
    for pid, p in pieces.items():
        art = p["art"]
        if p["kind"] == "식물":
            art.save(f"{out}/plants/{pid}.png")
            x, y = p["anchor"][0]
            cat["plants"][pid] = {"w": art.width, "h": art.height,
                                  "stemX": round(x), "stemY": round(y),
                                  "pot": DEFAULT_POT.get(pid, "pot_medium")}
            print(f"{pid:14} {art.width:5} {art.height:5}  밑동 ({x:.0f},{y:.0f})")
            continue

        art.save(f"{out}/pots/{pid}.png")
        boxy = pid in BOXY
        sh = (shadow(art.width * 1.02, iso, "diamond", ink=112, blur=.36)
              if boxy else shadow(art.width * .8, iso))
        sh.save(f"{out}/shadows/{pid}.png")
        fx, fy = p["foot"]
        cells = footprint(art.width * to_stage, grid["tileW"])
        cat["pots"][pid] = {
            "w": art.width, "h": art.height, "cells": cells,
            "foot": {"x": round(fx), "y": round(fy)},
            "slots": [{"x": round(x), "y": round(y), "grade": g}
                      for (x, y), g in zip(p["anchor"],
                                           slot_grades(pid, len(p["anchor"])))],
            "shadow": {"w": sh.width, "h": sh.height,
                       "anchorX": sh.width // 2, "anchorY": sh.height // 2,
                       "drop": round((art.height - fy) * .34) if boxy else 0},
        }
        print(f"{pid:14} {art.width:5} {art.height:5}  닿는자리 ({fx:.0f},{fy:.0f}) "
              f"· 심는자리 {len(p['anchor'])}곳 · {cells[0]}x{cells[1]}칸 "
              f"(무대 폭 {art.width * to_stage:.0f})")

    cat["names"] = NAMES
    json.dump(cat, open(f"{out}/catalog.json", "w"), indent=1, ensure_ascii=False)
    print(f"\n{out}/catalog.json · 화분 {len(cat['pots'])} · 식물 {len(cat['plants'])}")
    print(f"무대 타일 {grid['tileW']}x{grid['tileH']} · 조각 배율 {to_stage:.4f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
