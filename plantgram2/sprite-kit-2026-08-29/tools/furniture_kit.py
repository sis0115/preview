"""가구 시트에서 조각을 꺼냅니다.

이 시트는 알파가 들어 있어 배경을 지울 일이 없습니다. 덩어리로 나누고,
바닥에 닿는 자리만 재면 됩니다.

축척은 우리가 정하지 않습니다 - 두 시트에 함께 그린 **긴 화단**으로
맞춥니다(RULES 7). 조각 하나만 늘리지 않고 시트 전체에 한 값을 곱합니다.

돌아온 그림의 선반과 작업대에는 **화분과 식물이 그려져** 있습니다. 우리가
여유 높이를 보여 주려고 깔아 둔 흐린 화분을 내용으로 읽으셨습니다. 그래서
이 둘은 자리를 가진 그릇이 아니라 **장식 가구**로 씁니다 - 자리가 없으면
가구입니다.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, "tools")
from alpha_kit import pieces          # noqa: E402
from verify_spec import foot_of       # noqa: E402

SHEET = "sheets/furniture_art.png"

# 덩어리는 위→아래, 왼→오 순서로 돌아옵니다. 돌아온 그림이 2x2 로 다시
# 배치돼 왔으므로 안내 이미지의 칸 차례와 다릅니다.
ORDER = ["shelf_planted", "bench_planted", "palm_potted", "bed_new"]
KEEP = ["shelf_planted", "bench_planted"]     # 지금 쓸 것


def load(sheet=SHEET, bed_width=301.0):
    """{id: {art, foot}} 와 축척. [bed_width] 는 맞출 긴 화단의 폭입니다."""
    got = pieces(sheet)
    if len(got) != len(ORDER):
        raise SystemExit(f"조각이 {len(got)}개입니다. {len(ORDER)}개를 기대했습니다.")

    full = Image.open(sheet).convert("RGBA")
    al = np.asarray(full).astype(float)[..., 3] / 255
    solid = ndimage.binary_fill_holes(
        ndimage.binary_closing(al > .5, np.ones((9, 9))))
    lab, _ = ndimage.label(solid)

    bed = dict(zip(ORDER, got))["bed_new"][1]
    unit = bed_width / bed.width

    out = {}
    for pid, (box, art) in zip(ORDER, got):
        own = lab == lab[(box[1] + box[3]) // 2, (box[0] + box[2]) // 2]
        fx, fy = foot_of(own, box)
        k = unit
        a = art.resize((max(1, round(art.width * k)), max(1, round(art.height * k))),
                       Image.LANCZOS)
        out[pid] = dict(art=a, kind="화분", anchor=[],
                        foot=((fx - box[0]) * k, (fy - box[1]) * k))
    return out, unit


if __name__ == "__main__":
    got, unit = load()
    print(f"축척 {unit:.4f}  (긴 화단으로 맞춤)")
    for k, v in got.items():
        a = v["art"]
        print(f"  {k:15s} {a.width:4d}x{a.height:4d}  "
              f"닿는자리 ({v['foot'][0]:.0f},{v['foot'][1]:.0f})"
              f"{'   ← 씁니다' if k in KEEP else ''}")
