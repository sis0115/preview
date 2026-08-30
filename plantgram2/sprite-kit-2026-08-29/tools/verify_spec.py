"""돌아온 그림에서 조합에 쓸 점을 찾을 수 있는지 봅니다.

크기는 보지 않습니다. 한 장 안에서 그린 것끼리는 저절로 맞고, 무대에 얹을
때는 시트 전체를 한 배율로 줄이면 됩니다.

보는 것은 하나입니다 - **조합에 쓸 점을 그림에서 찾을 수 있는가.**

    화분 : 흙(심는 자리)과 바닥에 닿는 자리
    식물 : 줄기 밑동

십자와 얼마나 떨어졌는지는 참고로만 적습니다. 물체가 통째로 옮겨졌을 뿐이면
점도 함께 옮겨졌을 테니 문제가 아닙니다. 문제는 점을 못 찾는 경우입니다 -
잎이 밑동보다 아래로 내려가 있거나, 흙이 안 보이거나.

    python3 tools/verify_spec.py sheets/spec_04_art.png sheets/spec_04.json
"""
import colorsys
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

KEY = (255, 0, 255)


def alpha_of(im):
    """투명이면 알파를, 마젠타 배경이면 그 반대를 씁니다."""
    a = np.asarray(im.getchannel("A"))
    if a.min() < 200:
        return a > 110
    rgb = np.asarray(im.convert("RGB")).astype(int)
    return np.abs(rgb - np.array(KEY)).sum(2) > 120


def components(mask, least=3000):
    """물체 하나하나의 바깥 상자와 **그 물체만의 마스크**.

    네모로만 오리면 상자 안에 들어온 옆 물체까지 딸려 옵니다. 조각을 오릴
    때는 반드시 자기 덩어리로 걸러야 합니다.
    """
    lab, k = ndimage.label(ndimage.binary_closing(mask, np.ones((9, 9))))
    out = []
    for c in range(1, k + 1):
        ys, xs = np.nonzero(lab == c)
        if len(xs) < least:
            continue
        box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        out.append((box, lab == c))
    out.sort(key=lambda o: (o[0][1] // 400, o[0][0]))
    return out


def blobs(mask, least=3000):
    return [box for box, _ in components(mask, least)]


def stem_of(mask, box):
    """줄기 밑동.

    맨 아랫줄의 한가운데로 잡으면, 잎이 줄기보다 아래로 처진 식물에서 그
    잎끝으로 끌려갑니다(몬스테라가 30px 밀렸습니다).

    그래서 맨 아랫부분에서 **가장 넓은 덩어리**를 봅니다. 잎끝은 가늘게
    한 점으로 끝나고 줄기 뭉치는 굵습니다.
    """
    x0, y0, x1, y1 = box
    sub = mask[y0:y1 + 1, x0:x1 + 1]
    h = y1 - y0 + 1
    band = sub[int(h * .92):]
    lab, k = ndimage.label(band)
    best = None
    for c in range(1, k + 1):
        _, xs = np.nonzero(lab == c)
        if best is None or len(xs) > best[0]:
            best = (len(xs), (int(xs.min()) + int(xs.max())) / 2)
    ys, xs = np.nonzero(sub)
    if best is None:
        return (x0 + (int(xs.min()) + int(xs.max())) / 2, y0 + int(ys.max()))
    return (x0 + best[1], y0 + int(ys.max()))


def soil_of(im, mask, box):
    """흙. 갈색(붉은 계열, 어둡고 채도 있는 색)만 골라 무게중심을 냅니다."""
    x0, y0, x1, y1 = box
    rgb = np.asarray(im.convert("RGB")).astype(float)[y0:y1 + 1, x0:x1 + 1] / 255
    sub = mask[y0:y1 + 1, x0:x1 + 1]
    h, w, _ = rgb.shape
    flat = rgb.reshape(-1, 3)
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in flat])
    hue, sat, val = (hsv[:, i].reshape(h, w) for i in range(3))
    soil = sub & ((hue < .13) | (hue > .92)) & (sat > .18) & (val < .62)
    if soil.sum() < 200:
        return None
    ys, xs = np.nonzero(soil)
    return (x0 + xs.mean(), y0 + ys.mean(), int(soil.sum()))


def foot_of(mask, box):
    """바닥에 닿는 자리. 실루엣에서 아래로 튀어나온 곳을 찾습니다."""
    x0, y0, x1, y1 = box
    sub = mask[y0:y1 + 1, x0:x1 + 1]
    h, w = sub.shape
    low = np.full(w, -1)
    for x in range(w):
        ys = np.nonzero(sub[:, x])[0]
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
    if len(feet) >= 2 and abs(feet[-1][0] - feet[0][0]) > w * .35:
        (ax, ay), (bx, by) = feet[0], feet[-1]
        return (x0 + (ax + bx) / 2, y0 + (ay + by) / 2)
    bottom = int(low.max())
    width, cx = 0, w / 2
    for y in range(int(h * .75), h):
        xs = np.nonzero(sub[y])[0]
        if len(xs) == 0:
            continue
        span = int(xs.max()) - int(xs.min()) + 1
        if span > width:
            width, cx = span, (int(xs.min()) + int(xs.max())) / 2
    return (x0 + cx, y0 + bottom - width / 4)


def main(art, spec_path="sheets/spec_04.json", out=None):
    out = out or spec_path.replace(".json", "_check.png")
    spec = json.load(open(spec_path))
    im = Image.open(art).convert("RGBA")
    if im.size != (spec["width"], spec["height"]):
        print(f"크기가 다릅니다: {im.size} — 다시 받아야 합니다")
        return 1

    mask = alpha_of(im)
    got = blobs(mask)
    if len(got) != len(spec["items"]):
        print(f"물체가 {len(got)}개입니다 (있어야 할 수 {len(spec['items'])}) — "
              "겹쳤거나 빠졌습니다\n")

    guide = Image.open(spec_path.replace(".json", ".png")).convert("RGBA")
    chk = Image.alpha_composite(guide, im).convert("RGB")
    dr = ImageDraw.Draw(chk)
    bad = 0

    print(f"{'칸':2} {'이름':12} {'찾은 점':>18}  {'십자에서':>10}   판정")
    for it, g in zip(spec["items"], got):
        cx, cy = it["ground"]
        if it["kind"] == "식물":
            px, py = stem_of(mask, g)
            # 밑동이 그림에서 가장 아래에 있는지. 잎이 더 내려가면 끌려갑니다.
            centred = abs(px - (g[0] + g[2]) / 2) < (g[2] - g[0]) * .30
            ok, why = centred, "" if centred else "밑동이 한쪽으로 치우침"
            what = "줄기 밑동"
        else:
            # 가구는 흙이 없습니다. 닿는 자리만 봅니다.
            s = soil_of(im, mask, g) if it["kind"] == "화분" else None
            px, py = foot_of(mask, g)
            ok = s is not None or it["kind"] != "화분"
            why = "" if ok else "흙이 안 보임"
            what = "닿는 자리"
            if s:
                dr.ellipse([s[0] - 7, s[1] - 7, s[0] + 7, s[1] + 7],
                           outline=(60, 110, 220), width=3)
        bad += 0 if ok else 1
        color = (40, 150, 80) if ok else (205, 70, 45)
        dr.line([(px - 14, py), (px + 14, py)], fill=color, width=3)
        dr.line([(px, py - 14), (px, py + 14)], fill=color, width=3)
        print(f"{it['cell'] + 1:2} {it['id']:12} {what:>12}"
              f" {px - cx:+5.0f} {py - cy:+5.0f}"
              + ("        찾음" if ok else f"     {why}"))

    chk.save(out)
    print(f"\n{out} — 초록/빨강 십자 = 찾은 닿는 점, 파란 동그라미 = 찾은 흙")
    print("크기는 보지 않습니다. 십자에서 떨어진 값은 참고입니다 — "
          "물체가 통째로 옮겨진 것이면 점도 함께 옮겨집니다.")
    print(f"{len(spec['items']) - bad}/{len(spec['items'])} 에서 점을 찾았습니다")
    if bad:
        print("\n점을 못 찾은 칸이 있습니다. 그 칸만 다시 그려 달라고 하세요.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
