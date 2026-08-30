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

SHEET_TILE = 225.0

NAMES = {
    "pot_sprout": "새싹 화분", "pot_small": "소형 화분",
    "pot_medium": "중형 화분", "pot_large": "대형 화분",
    "pot_xlarge": "특대형 화분", "bed_long": "긴 화단",
    "shelf": "선반", "planter_big": "석재 화분",
    "sprout": "새싹", "small": "소형", "medium": "중형",
    "large": "대형", "xlarge": "특대형",
}
BOXY = {"bed_long", "shelf", "planter_big"}


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
                                  "stemX": round(x), "stemY": round(y)}
            print(f"{pid:14} {art.width:5} {art.height:5}  밑동 ({x:.0f},{y:.0f})")
            continue

        art.save(f"{out}/pots/{pid}.png")
        boxy = pid in BOXY
        sh = (shadow(art.width * 1.02, iso, "diamond", ink=112, blur=.36)
              if boxy else shadow(art.width * .8, iso))
        sh.save(f"{out}/shadows/{pid}.png")
        fx, fy = p["foot"]
        cat["pots"][pid] = {
            "w": art.width, "h": art.height,
            "foot": {"x": round(fx), "y": round(fy)},
            "slots": [{"x": round(x), "y": round(y)} for x, y in p["anchor"]],
            "shadow": {"w": sh.width, "h": sh.height,
                       "anchorX": sh.width // 2, "anchorY": sh.height // 2,
                       "drop": round((art.height - fy) * .34) if boxy else 0},
        }
        print(f"{pid:14} {art.width:5} {art.height:5}  닿는자리 ({fx:.0f},{fy:.0f}) "
              f"· 심는자리 {len(p['anchor'])}곳")

    cat["names"] = NAMES
    json.dump(cat, open(f"{out}/catalog.json", "w"), indent=1, ensure_ascii=False)
    print(f"\n{out}/catalog.json · 화분 {len(cat['pots'])} · 식물 {len(cat['plants'])}")
    print(f"무대 타일 {grid['tileW']}x{grid['tileH']} · 조각 배율 {to_stage:.4f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
