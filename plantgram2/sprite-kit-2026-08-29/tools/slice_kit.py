"""받은 예제 한 벌을 잘라 Flutter 앱이 쓸 에셋으로 내보냅니다.

기준점은 그림에서 잽니다. kit_ref.json 의 표시는 "여기에 그려 달라"는
요청일 뿐 실제로 그려진 자리가 아니라서, 흙은 색으로 줄기는 밑동 폭으로
찾고 표시는 못 찾았을 때의 대비로만 씁니다. 그림자는 요청하지 않고 여기서
그립니다 - 화분마다 폭을 맞출 수 있고 부드러운 타원이라 코드가 더 정확합니다.

    python3 tools/slice_kit.py sheets/kit.png ../app-kit/assets
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage


def biggest_blob(im, alpha_min=110, gap=4):
    """가장 큰 덩어리만 남깁니다.

    칸 경계를 넘어온 옆 조각의 잎끝이나 다리가 함께 잘려 옵니다. 네모로만
    오리면 그것들이 붙어 오므로, 자기 덩어리가 아닌 픽셀을 지웁니다.
    """
    a = np.asarray(im.getchannel("A")) > alpha_min
    if not a.any():
        return im
    # 살짝 부풀려 안티에일리어싱으로 끊긴 부분을 한 덩어리로 묶습니다
    grown = ndimage.binary_dilation(a, iterations=gap)
    lab, n = ndimage.label(grown)
    if n <= 1:
        return im
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    keep = lab == (int(np.argmax(sizes)) + 1)
    arr = np.array(im)
    arr[~keep, 3] = 0
    return Image.fromarray(arr, "RGBA")


def trim(im, pad=4, alpha_min=110):
    """불투명 영역만 남기고 오립니다. 잘라낸 만큼의 이동량도 돌려줍니다.

    문턱을 높게 잡습니다. 생성 이미지는 물체 둘레에 옅은 후광(alpha 1~60)
    을 남기는데, 낮게 잡으면 그 후광까지 물체로 세어 칸 전체가 잡힙니다.
    """
    bb = im.getchannel("A").point(lambda v: 255 if v > alpha_min else 0).getbbox()
    if bb is None:
        return im, 0, 0
    x0 = max(0, bb[0] - pad)
    y0 = max(0, bb[1] - pad)
    x1 = min(im.width, bb[2] + pad)
    y1 = min(im.height, bb[3] + pad)
    return im.crop((x0, y0, x1, y1)), x0, y0


def hue_sat(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0, 0.0
    h = ((g - b) / d % 6) if mx == r else ((b - r) / d + 2) if mx == g else ((r - g) / d + 4)
    return h / 6, d / mx


def find_soil(im, slots):
    """그림 안에서 실제 흙 자리를 찾습니다.

    표시한 자리를 그대로 믿지 않습니다. 생성기가 화분을 표시보다 아래에
    그리면 흙 자리가 그림 밖으로 나가 식물이 공중에 뜹니다. 흙은 어둡고
    붉은 갈색이라 눈으로 찾는 편이 확실합니다.

    심는 자리가 둘인 긴 화단은 찾은 흙을 좌우로 갈라 둘로 나눕니다.
    """
    px = im.load()
    pts = []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 120:
                continue
            h, sa = hue_sat(r, g, b)
            if max(r, g, b) / 255 < .62 and sa > .18 and (h < .13 or h > .92):
                pts.append((x, y))
    if not pts:
        return slots

    def summarize(group):
        xs = [q[0] for q in group]
        ys = [q[1] for q in group]
        return {"x": round(sum(xs) / len(xs)), "y": round(sum(ys) / len(ys)),
                "w": max(xs) - min(xs)}

    if len(slots) == 1:
        return [summarize(pts)]

    # 여러 자리는 흙을 가로로 고르게 나눕니다.
    #
    # x 중앙값으로 반을 가르면 등각 상자에서 좌우가 고르지 않게 갈립니다
    # (한쪽이 91, 다른 쪽이 126 으로 나왔습니다). 흙의 가로 범위를 자리
    # 수만큼 등분하고, 각 구간의 흙 픽셀만으로 자리를 잡습니다.
    n = len(slots)
    xs_all = [q[0] for q in pts]
    lo, hi = min(xs_all), max(xs_all)
    span = (hi - lo) / n
    out = []
    for k in range(n):
        a, b = lo + k * span, lo + (k + 1) * span
        band = [q for q in pts if a <= q[0] <= b] or pts
        ys = [q[1] for q in band]
        out.append({
            "x": round(a + span / 2),
            "y": round(sum(ys) / len(ys)),
            # 자리 폭은 등분한 구간. 여기에 맞춰 식물을 줄입니다.
            "w": round(span * .92),
        })
    return out


def find_foot(im, alpha_min=110):
    """화분이 바닥에 닿는 자리. 칸 한가운데에 놓을 점입니다.

    지금까지는 흙 높이를 칸 한가운데에 놓았습니다. 흙은 화분 위쪽이라,
    키가 큰 화단일수록 다리가 제 칸보다 한참 앞으로 나갔습니다.

    바닥 실루엣에서 아래로 튀어나온 곳을 찾습니다. 다리가 달린 화단이면
    양 끝 다리가 밑면의 마주 보는 두 꼭짓점이므로 그 한가운데가 답입니다.
    둥근 화분은 튀어나온 곳이 하나뿐이라, 등각에서 바닥 자국의 높이가
    폭의 절반이라는 것으로 한가운데를 잡습니다.
    """
    a = np.asarray(im.getchannel("A")) > alpha_min
    h, w = a.shape
    low = np.full(w, -1)
    for x in range(w):
        ys = np.nonzero(a[:, x])[0]
        if len(ys):
            low[x] = ys.max()

    feet = []
    for x in range(w):
        if low[x] < 0:
            continue
        if low[x] == low[max(0, x - 12):x + 13].max():
            if not feet or x - feet[-1][0] > 18:
                feet.append((x, int(low[x])))
            elif low[x] > feet[-1][1]:
                feet[-1] = (x, int(low[x]))

    # 다리로 보려면 양 끝이 충분히 떨어져 있어야 합니다. 둥근 화분의
    # 평평한 밑동도 돌출 두 곳으로 잡히지만 몇 픽셀 차이뿐입니다.
    if len(feet) >= 2 and abs(feet[-1][0] - feet[0][0]) > w * .35:
        (x0, y0), (x1, y1) = feet[0], feet[-1]
        return {"x": round((x0 + x1) / 2), "y": round((y0 + y1) / 2),
                "w": abs(x1 - x0)}

    bottom = int(low.max())
    # 밑동 타원의 허리 - 아랫부분에서 가장 넓은 줄입니다.
    width, x = 0, w / 2
    for y in range(int(h * .75), h):
        xs = np.nonzero(a[y])[0]
        if len(xs) == 0:
            continue
        span = int(xs.max()) - int(xs.min()) + 1
        if span > width:
            width, x = span, (int(xs.min()) + int(xs.max())) / 2
    # 바닥 자국은 폭의 절반 높이. 그 절반 위가 한가운데입니다.
    return {"x": round(x), "y": round(bottom - width / 4), "w": int(width)}


def find_span(slots, st):
    """이 화분이 덮는 칸. 심는 자리가 놓인 방향을 격자의 축과 대 봅니다.

    자리가 하나면 한 칸입니다. 둘이면 두 칸이고, 어느 쪽으로 뻗는지는
    자리 사이 방향에 가장 가까운 축으로 정합니다. 앞뒤·좌우를 손으로
    정하지 않으므로, 화단을 다시 그려 방향이 뒤집혀도 따라옵니다."""
    if len(slots) < 2:
        return [[0, 0]]
    dx = slots[-1]["x"] - slots[0]["x"]
    dy = slots[-1]["y"] - slots[0]["y"]
    n = math.hypot(dx, dy)
    best, score = [0, 1], -2.0
    for si, sj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ax = st["uX"] * si + st["vX"] * sj
        ay = st["uY"] * si + st["vY"] * sj
        c = (dx * ax + dy * ay) / (n * math.hypot(ax, ay))
        if c > score:
            score, best = c, [si, sj]
    return [[best[0] * k, best[1] * k] for k in range(len(slots))]


def find_stem(im, mark):
    """줄기가 흙에 닿는 자리를 그림에서 찾습니다.

    표시선을 그대로 쓰지 않습니다. 생성기가 식물을 칸 한가운데에 정확히
    그리지 않으면 표시와 실제 줄기가 5~17px 어긋나고, 그만큼 식물이
    화분에서 밀립니다. 화분의 흙을 찾아 쓰면서 식물만 표시를 믿을
    이유가 없습니다.

    맨 아랫부분 몇 줄의 불투명 폭 한가운데가 줄기입니다. 잎은 위로
    벌어지므로 아래쪽만 보면 줄기만 남습니다.
    """
    a = np.asarray(im.getchannel("A")) > 110
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return mark
    bottom = int(ys.max())
    rows = max(8, round(im.height * .04))
    sel = xs[ys > bottom - rows]
    return {"x": round((int(sel.min()) + int(sel.max())) / 2), "y": bottom}


def make_shadow(width, path):
    """접지 그림자. 진한 반투명이라 어떤 바닥에서도 얼룩이 되지 않습니다."""
    w = round(width * 1.25)
    h = round(w / 2.6)
    pad = round(w * .3)
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([pad, pad, pad + w, pad + h],
                               fill=(64, 52, 38, 70))
    im = im.filter(ImageFilter.GaussianBlur(pad * .38))
    im.save(path)
    return {"w": im.width, "h": im.height,
            "anchorX": im.width // 2, "anchorY": im.height // 2}


def main(sheet_path, out="assets", ref="sheets/kit_ref.json"):
    m = json.load(open(ref))
    sheet = Image.open(sheet_path).convert("RGBA")
    if sheet.size != (m["width"], m["height"]):
        sheet = sheet.resize((m["width"], m["height"]), Image.LANCZOS)
        print(f"크기를 {sheet.size} 로 맞췄습니다")

    for d in ("greenhouse", "pots", "plants", "shadows"):
        os.makedirs(f"{out}/{d}", exist_ok=True)

    st = m["stage"]
    stage = sheet.crop((st["x"], st["y"], st["x"] + st["w"], st["y"] + st["h"]))
    # 알파를 살립니다. RGB 로 바꾸면 투명한 둘레가 검게 굳습니다.
    stage.save(f"{out}/greenhouse/stage.png")

    # 격자는 바닥 네 꼭짓점에서 잰 값을 그대로 넘깁니다. 마름모가 살짝
    # 기울어도 (i, j) 두 방향 벡터로 두면 정확합니다.
    cat = {"pots": {}, "plants": {}, "grid": {
        "iso": m["iso"], "n": st["grid"],
        "tileW": st["tileW"], "tileH": st["tileH"],
        "topX": st["topX"], "topY": st["topY"],
        "uX": st["uX"], "uY": st["uY"], "vX": st["vX"], "vY": st["vY"],
        "sceneW": st["w"], "sceneH": st["h"]}}

    for p in m["pieces"]:
        x0, y0, x1, y1 = p["box"]
        cell = biggest_blob(sheet.crop((x0, y0, x1, y1)))
        art, dx, dy = trim(cell)
        # 후광은 지웁니다. 남기면 타일 위에서 뿌연 테로 보입니다.
        art.putalpha(art.getchannel("A").point(lambda v: 0 if v < 60 else v))
        if p["kind"] == "pot":
            # 심는 자리를 오려낸 그림 안의 좌표로 옮깁니다
            slots = find_soil(art, p["slots"])
            foot = find_foot(art)
            art.save(f"{out}/pots/{p['id']}.png")
            cat["pots"][p["id"]] = {
                "w": art.width, "h": art.height, "slots": slots,
                "span": find_span(slots, st),
                "foot": {"x": foot["x"], "y": foot["y"]},
                # 그림자는 밑동 폭에 맞춥니다. 긴 화단은 심는 자리 하나가
                # 아니라 다리 사이 전체에 그늘이 집니다.
                "shadow": make_shadow(foot["w"] * .92,
                                      f"{out}/shadows/{p['id']}.png"),
            }
        else:
            a = p["anchor"]
            art.save(f"{out}/plants/{p['id']}.png")
            stem = find_stem(art, {"x": a["x"] - x0 - dx,
                                   "y": min(a["y"] - y0 - dy, art.height)})
            cat["plants"][p["id"]] = {
                "w": art.width, "h": art.height,
                "stemX": stem["x"], "stemY": stem["y"],
            }
        print(f"  {p['id']:16} {art.width:4}x{art.height:<4}")

    # 조각은 아래 칸에 크게 그려져 있고 무대의 타일은 작습니다. 한 배율로
    # 묶습니다.
    #
    # 63.5 는 눈으로 맞춘 값입니다. 온실 안에 이미 그려진 작업대 화분과
    # 선반 화분에 견주어, 표준 화분이 무대에서 차지할 폭을 정했습니다.
    # 처음에 0.62 로 잡았더니 식물이 지붕을 뚫었습니다.
    #
    # 예전에는 이 값을 타일 폭의 비율로 두었는데, 그러면 바닥을 몇 칸으로
    # 나누느냐에 따라 식물 크기까지 흔들립니다. 칸 수는 우리가 정하는 것이고
    # 화분 크기는 그림에 이미 정해져 있으므로, 그림 쪽에 붙여 둡니다.
    POT_ON_STAGE = 63.5
    ref = next((v for k, v in cat["pots"].items() if not k.startswith("bed")),
               next(iter(cat["pots"].values())))
    cat["grid"]["unitScale"] = round(POT_ON_STAGE / ref["w"], 4)
    print(f"  한 배율 {cat['grid']['unitScale']}  "
          f"(표준 화분 폭 {ref['w']} → 무대에서 {POT_ON_STAGE}px)")

    json.dump(cat, open(f"{out}/catalog.json", "w"), indent=1, ensure_ascii=False)
    print(f"\n무대 {stage.width}x{stage.height} · 화분 {len(cat['pots'])} · "
          f"식물 {len(cat['plants'])} → {out}/catalog.json")


if __name__ == "__main__":
    main(*sys.argv[1:])
