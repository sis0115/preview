"""빈 가구 시트에서 조각을 꺼냅니다.

이 시트는 알파가 들어 있고(투명 77% · 잔재 0.00%) 판 위가 비어 있어,
드디어 **자리를 가진 가구**로 쓸 수 있습니다.

축척은 두 시트에 함께 그린 긴 화단으로 맞춥니다(RULES 7).

자리는 그림에서 찾아내지 않습니다(RULES 4). 부탁한 높이는 그림에
없었습니다 - 위층을 훨씬 낮게 그려 오셨습니다. 대신 **상자와 격자만으로**
윗판을 되돌려 읽습니다: 맨 위 점이 윗면의 먼 꼭짓점이고, 거기서 반 칸
내려오면 윗면 한가운데입니다. 자리는 덮은 칸들의 한가운데를 그 높이로
올린 점입니다.

아래층 판은 상자만으로는 높이를 알 수 없어 아직 자리를 두지 않습니다.
"""
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, "tools")
from fit_furniture import load as fit          # noqa: E402
from verify_spec import stem_of                # noqa: E402

FURNITURE = ["shelf_two", "bench"]
PLANT = {"xlarge": "xlarge"}                   # 조각 id → 식물 id


def load(bed_in_kit=301.0, kit_to_stage=None):
    got, art_to_kit, _ = fit(bed_in_kit=bed_in_kit, kit_to_stage=kit_to_stage)

    def scaled(im):
        return im.resize((max(1, round(im.width * art_to_kit)),
                          max(1, round(im.height * art_to_kit))), Image.LANCZOS)

    out = {}
    for pid in FURNITURE:
        p = got[pid]
        out[pid] = dict(
            art=scaled(p["art"]), kind="화분",
            foot=(p["foot"][0] * art_to_kit, p["foot"][1] * art_to_kit),
            anchor=[(s["x"] * art_to_kit, s["y"] * art_to_kit)
                    for s in p["slots"]],
            grades=[s["grade"] for s in p["slots"]])

    for src, pid in PLANT.items():
        art = scaled(got[src]["art"])
        m = np.asarray(art).astype(float)[..., 3] / 255 > .5
        x, y = stem_of(m, (0, 0, art.width, art.height))
        out[pid] = dict(art=art, kind="식물", anchor=[(x, y)])
    return out, art_to_kit


if __name__ == "__main__":
    got, unit = load()
    print(f"축척 {unit:.4f}  (긴 화단으로 맞춤)")
    for k, v in got.items():
        a = v["art"]
        print(f"  {k:12s} {a.width:4d}x{a.height:4d}  {v['kind']}  "
              f"기준점 {[(round(x), round(y)) for x, y in v['anchor']]}"
              + (f"  등급 {v['grades']}" if "grades" in v else ""))
