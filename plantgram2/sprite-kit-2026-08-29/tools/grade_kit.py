"""등급 시트에서 조각과 기준점을 꺼냅니다.

새 시트는 이전 시트와 축척이 저절로 맞지 않습니다(RULES 7). 두 시트에 함께
그린 긴 화단으로 비율을 구해, 새 시트 **전체**에 같은 값을 곱합니다 -
조각 하나만 늘리는 것이 아닙니다.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, "tools")
from verify_spec import stem_of, foot_of      # noqa: E402
from compose_test import soils, cut           # noqa: E402

BED_ON_OLD_SHEET = 301          # 이전 시트에서 잰 긴 화단 폭

POTS = ["pot_sprout", "pot_small", "pot_medium", "pot_large", "pot_xlarge",
        "bed_long"]
PLANTS = ["sprout", "small", "medium", "large", "xlarge"]


def keyed(path):
    """체커보드를 지우고 알파를 만듭니다.

    투명으로 달라고 했지만 체커보드가 **그려져** 왔습니다. 체커보드는 무채색
    이고 아주 밝으므로, 채도와 어두움으로 알파를 뽑습니다.

    0/1 로 자르면 잎 가장자리가 톱니처럼 남습니다. 부드럽게 이어지도록
    두 값 사이를 비례로 채웁니다.
    """
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    soft = np.clip(np.maximum(sat / .09, (.96 - mx) / .10), 0, 1)
    # 체커보드가 두 가지 밝기로 번갈아 있어 가장자리에서 알파가 한 칸씩
    # 튑니다. 작은 중앙값 필터로 그 무늬만 지웁니다.
    soft = ndimage.median_filter(soft, 3)

    # 두 가지 마스크가 필요합니다. 섞으면 안 됩니다.
    #
    #  · 묶는 마스크 - 조각 하나하나의 바깥 상자를 찾는 데 씁니다. 잎 사이가
    #    끊겨 있으면 한 식물이 여러 덩어리로 쪼개지므로 넉넉히 메웁니다.
    #  · 알파 - 실제로 보이는 부분입니다. 여기서 메우면 야자 잎 사이의 틈이
    #    흰 종이처럼 막힙니다. 틈은 배경이지 물체가 아닙니다.
    raw = soft > .5
    group = ndimage.binary_fill_holes(
        ndimage.binary_closing(raw, np.ones((13, 13))))
    lab, k = ndimage.label(group)
    sz = ndimage.sum(group, lab, range(1, k + 1))
    keep = np.isin(lab, [i + 1 for i in range(k) if sz[i] >= 400])

    # 0/1 로 자르면 잎 가장자리 픽셀이 불투명한 채로 남아 흰 테가 집니다.
    # 살짝 번지게 해서 가장자리에 중간값을 주고, 경계를 안쪽으로 당깁니다.
    alpha = ndimage.gaussian_filter(raw.astype(float), .9)
    alpha = np.clip((alpha - .38) / .44, 0, 1)
    alpha = np.where(keep, alpha, 0)       # 묶인 조각 밖의 얼룩은 버립니다

    alpha = np.clip(alpha, 0, 1)

    # 가장자리 픽셀에는 체커보드 색이 섞여 있습니다. 관측색 C = a·F + (1-a)·B
    # 이므로, 배경 B 를 알면 원래 색 F 를 되돌릴 수 있습니다.
    bg = a[alpha < .05]
    B = np.median(bg, 0) if len(bg) else np.array([1., 1., 1.])
    aa = np.maximum(alpha, .06)[..., None]
    F = np.clip((a - (1 - aa) * B) / aa, 0, 1)
    rgb = np.where(alpha[..., None] > .995, a, F)

    out = Image.fromarray((rgb * 255).astype("uint8"), "RGB").convert("RGBA")
    out.putalpha(Image.fromarray((alpha * 255).astype("uint8")))
    return out, keep, lab


def load(path="sheets/grade_art.png"):
    im, mask, lab = keyed(path)
    parts = []
    for c in np.unique(lab[mask]):
        ys, xs = np.nonzero((lab == c) & mask)
        if len(xs) < 400:
            continue
        parts.append(((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
                      (lab == c) & mask))
    top = [p for p in parts if p[0][1] < 500]
    bot = [p for p in parts if p[0][1] >= 500]
    top.sort(key=lambda p: p[0][0])
    bot.sort(key=lambda p: p[0][0])

    piece = {}
    for name, (g, own) in zip(POTS, top):
        want = 2 if name == "bed_long" else 1
        fx, fy = foot_of(own, g)
        piece[name] = dict(art=cut(im, own, g), kind="화분",
                           foot=(fx - g[0], fy - g[1]),
                           anchor=[(x - g[0], y - g[1])
                                   for x, y in soils(im, own, g, want)])
    for name, (g, own) in zip(PLANTS, bot):
        x, y = stem_of(own, g)
        piece[name] = dict(art=cut(im, own, g), kind="식물",
                           anchor=[(x - g[0], y - g[1])])

    unit = BED_ON_OLD_SHEET / piece["bed_long"]["art"].width
    return piece, unit


def scaled(p, k):
    """조각 하나를 배율 k 로. 기준점도 같이 옮깁니다."""
    a = p["art"]
    art = a.resize((max(1, round(a.width * k)), max(1, round(a.height * k))),
                   Image.LANCZOS)
    out = dict(art=art, kind=p["kind"],
               anchor=[(x * k, y * k) for x, y in p["anchor"]])
    if "foot" in p:
        out["foot"] = (p["foot"][0] * k, p["foot"][1] * k)
    return out
