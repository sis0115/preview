"""돌아온 가구 그림에 우리가 부탁한 자리를 얹어 봅니다.

자리를 그림에서 **찾아내지** 않습니다(RULES 4). 우리가 안내 이미지에 찍어
보낸 자리를, 조각마다 재서 나온 축척과 닿는 자리로 되돌려 놓을 뿐입니다.

  · 축척  두 시트에 함께 그린 긴 화단으로. 조각 하나만 늘리지 않습니다.
  · 자리  안내 이미지의 (자리 - 닿는 점) 을 그 축척으로 옮깁니다.

그리고 **눈으로 검사합니다** - 판 윗면이 그 점을 지나가는지. 어긋나면
흡수하지 않고 다시 받습니다(RULES 5).

    python3 tools/fit_furniture.py
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from alpha_kit import pieces              # noqa: E402
from verify_spec import foot_of           # noqa: E402
from scipy import ndimage                 # noqa: E402

ART = "sheets/furniture_art2.png"
GUIDE = "sheets/furniture_sheet2.json"
FONT = "../app-kit/assets/fonts/{}.otf"
INK, DIM = (34, 40, 44), (120, 130, 138)
MARK, SLOT = (232, 106, 30), (24, 150, 96)

# 돌아온 그림의 덩어리는 왼→오 순서입니다. 안내 이미지의 칸 차례와 같습니다.
ORDER = ["shelf_two", "bench", "xlarge", "bed_long"]

# 윗판에 자리를 두는 조각과 그 등급. 아래층 판은 우리 격자만으로는
# 높이를 알 수 없어 아직 자리를 두지 않습니다.
PLATES = {"shelf_two": "small", "bench": "small"}
BED_IN_KIT = 301.0        # 4차 시트 좌표계에서의 긴 화단 폭


def font(s, b=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if b else "Pretendard-Regular"), s)


def load(sheet=ART, bed_in_kit=BED_IN_KIT, kit_to_stage=None):
    """조각과, 윗판 위의 자리를 돌려줍니다.

    부탁한 자리 높이는 그림에 없었습니다 - 위층을 훨씬 낮게 그려 오셨습니다.
    그렇다고 판을 눈으로 찾아 나서지는 않습니다(RULES 4). 대신 **상자와
    격자만으로** 윗판을 되돌려 읽습니다.

      · 조각의 맨 위 점 = 윗판 윗면의 먼 꼭짓점
      · 윗면은 밑면과 같은 평행사변형이므로, 거기서 반 칸 내려오면
        윗면 한가운데
      · 밑면 한가운데(닿는 자리)에서 그만큼이 판 높이

    자리는 덮은 칸들의 한가운데를 그 높이로 올린 점입니다. 찾아낸 것이
    아니라 우리 격자에서 계산한 것입니다.
    """
    got = pieces(sheet)
    if len(got) != 4:
        raise SystemExit(f"조각이 {len(got)}개입니다. 4개를 기대했습니다.")
    full = Image.open(sheet).convert("RGBA")
    al = np.asarray(full).astype(float)[..., 3] / 255
    solid = ndimage.binary_fill_holes(
        ndimage.binary_closing(al > .5, np.ones((9, 9))))
    lab, _ = ndimage.label(solid)

    grid = json.load(open("../app-kit/assets/catalog.json",
                          encoding="utf-8"))["grid"]
    if kit_to_stage is None:
        kit_to_stage = grid["unitScale"]
    bed = dict(zip(ORDER, got))["bed_long"][1]
    art_to_kit = bed_in_kit / bed.width
    art_to_stage = art_to_kit * kit_to_stage          # 그림 → 무대
    U = np.array([grid["uX"], grid["uY"]]) / art_to_stage   # 그림 좌표에서의 한 칸
    V = np.array([grid["vX"], grid["vY"]]) / art_to_stage

    out = {}
    for pid, (box, art) in zip(ORDER, got):
        own = lab == lab[(box[1] + box[3]) // 2, (box[0] + box[2]) // 2]
        fx, fy = foot_of(own, box)
        foot = np.array([fx - box[0], fy - box[1]], float)

        m = np.asarray(art).astype(float)[..., 3] / 255 > .5
        ys, xs = np.nonzero(m)
        near = xs[ys > ys.max() - 3]
        xb = (near.min() + near.max()) / 2
        left = (xb - xs.min()) / abs(U[0])
        right = (xs.max() - xb) / abs(V[0])
        step = lambda n: max(1, int(n + .75))              # noqa: E731
        cells = [step(left), step(right)]

        slots = []
        if pid in PLATES:
            # 윗면 한가운데의 화면 높이 = 맨 위 점 + 반 칸
            half = (cells[0] * abs(U[1]) + cells[1] * abs(V[1])) / 2
            top = ys.min() + half
            # 덮은 칸들의 한가운데를 그 높이로. 두 칸이면 ±반 칸 벌어집니다.
            axis = U if cells[0] > cells[1] else V
            n = max(cells)
            for k in range(n):
                off = axis * (k - (n - 1) / 2)
                slots.append({"grade": PLATES[pid],
                              "x": float(foot[0] + off[0]),
                              "y": float(top + off[1])})
        out[pid] = dict(art=art, foot=tuple(foot), cells=cells, slots=slots)
    return out, art_to_kit, art_to_stage


def main(out="sheets/furniture_fit.png"):
    got, art_to_kit, art_to_stage = load()
    W, H = 1560, 640
    im = Image.new("RGBA", (W, H), (244, 243, 239, 255))
    d = ImageDraw.Draw(im)
    d.text((36, 26), "부탁한 자리를 돌아온 그림에 얹어 본 것",
           font=font(30, True), fill=INK)
    d.text((36, 66), f"긴 화단으로 잰 축척 — 그림 → 무대 {art_to_stage:.4f}     "
                     "초록 십자는 상자와 격자만으로 되돌려 읽은 윗판 자리입니다",
           font=font(16), fill=DIM)

    x = 36
    for pid in ORDER:
        p = got[pid]
        a = p["art"].copy()
        dr = ImageDraw.Draw(a)
        for n, s in enumerate(p["slots"], 1):
            sx, sy = s["x"], s["y"]
            dr.line([(sx - 13, sy), (sx + 13, sy)], fill=SLOT, width=3)
            dr.line([(sx, sy - 13), (sx, sy + 13)], fill=SLOT, width=3)
            dr.text((sx + 16, sy - 8), f"{n}·{s['grade']}", font=font(13, True),
                    fill=SLOT)
        fx, fy = p["foot"]
        dr.line([(fx - 13, fy), (fx + 13, fy)], fill=MARK, width=3)
        dr.line([(fx, fy - 13), (fx, fy + 13)], fill=MARK, width=3)
        im.alpha_composite(a, (x, 130))
        d.text((x, 130 + a.height + 12),
               f"{pid} · {p['cells'][0]}x{p['cells'][1]}칸 · 자리 {len(p['slots'])}개",
               font=font(15, True), fill=INK)
        x += a.width + 24

    im.convert("RGB").save(out)
    print(out)
    for pid in ORDER:
        p = got[pid]
        print(f"  {pid:10s} {p['art'].width:4d}x{p['art'].height:4d} "
              f"{p['cells'][0]}x{p['cells'][1]}칸 "
              f"닿는자리 ({p['foot'][0]:.0f},{p['foot'][1]:.0f}) "
              f"자리 {[(round(s['x']), round(s['y'])) for s in p['slots']]}")


if __name__ == "__main__":
    main(*sys.argv[1:])
