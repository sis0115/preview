"""받은 예제 한 벌을 잘라 Flutter 앱이 쓸 에셋으로 내보냅니다.

기준점을 찾지 않습니다. 우리가 그려 보낸 자리가 kit_ref.json 에 있으므로
그대로 씁니다. 그림자는 요청하지 않고 여기서 그립니다 - 화분마다 폭을
맞출 수 있고 부드러운 타원이라 코드가 더 정확합니다.

    python3 tools/slice_kit.py sheets/kit.png ../app-kit/assets
"""
import json, os, sys
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
    mid = sum(q[0] for q in pts) / len(pts)
    halves = [[q for q in pts if q[0] < mid], [q for q in pts if q[0] >= mid]]
    return [summarize(g or pts) for g in halves]


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
            art.save(f"{out}/pots/{p['id']}.png")
            cat["pots"][p["id"]] = {
                "w": art.width, "h": art.height, "slots": slots,
                "bottom": art.height,
                "shadow": make_shadow(slots[0]["w"],
                                      f"{out}/shadows/{p['id']}.png"),
            }
        else:
            a = p["anchor"]
            art.save(f"{out}/plants/{p['id']}.png")
            # 밑동은 표시한 자리를 쓰되, 그림 밖으로 나가면 밑변으로
            # 당깁니다. 잎이 표시선 위에서 끝나는 경우가 있습니다.
            cat["plants"][p["id"]] = {
                "w": art.width, "h": art.height,
                "stemX": a["x"] - x0 - dx,
                "stemY": min(a["y"] - y0 - dy, art.height),
            }
        print(f"  {p['id']:16} {art.width:4}x{art.height:<4}")

    # 조각은 아래 칸에 크게 그려져 있고 무대의 타일은 작습니다. 한 배율로
    # 묶습니다.
    #
    # 0.34 는 눈으로 맞춘 값입니다. 온실 안에 이미 그려진 작업대 화분과
    # 선반 화분에 견주어 정했습니다. 처음에 0.62 로 잡았더니 식물이 지붕을
    # 뚫었습니다 - 타일이 크고 식물이 작은 것이 이 그림의 비율입니다.
    ref = next((v for k, v in cat["pots"].items() if not k.startswith("bed")),
               next(iter(cat["pots"].values())))
    cat["grid"]["unitScale"] = round(
        st["tileW"] * 0.62 / ref["slots"][0]["w"], 4)
    print(f"  한 배율 {cat['grid']['unitScale']}  "
          f"(타일 {st['tileW']} · 표준 화분 흙 {ref['slots'][0]['w']})")

    json.dump(cat, open(f"{out}/catalog.json", "w"), indent=1, ensure_ascii=False)
    print(f"\n무대 {stage.width}x{stage.height} · 화분 {len(cat['pots'])} · "
          f"식물 {len(cat['plants'])} → {out}/catalog.json")


if __name__ == "__main__":
    main(*sys.argv[1:])
