"""진짜 알파가 담겨 온 시트에서 조각을 꺼냅니다.

이번 시트는 처음으로 알파가 들어 있습니다(투명 71% · 불투명 23%).
지울 배경이 없으니 키잉도 필요 없습니다 - 덩어리로 나누기만 하면 됩니다.

어두운 바탕에서 보면 가장자리에 형광 테가 진 것처럼 보입니다. 밝은 바닥
위에 5배로 얹어 확인해 보니 테가 없었습니다. 눈으로 본 것이 아니라 쓸
자리에 얹어 보고 판단합니다. [clean] 은 정말 테가 질 때만 씁니다 -
가장자리 색을 가까운 불투명 픽셀 것으로 갈아 끼웁니다.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def clean(im):
    a = np.asarray(im.convert("RGBA")).astype(float) / 255
    al = a[..., 3]
    solid = al > .92
    if not solid.any():
        return im
    # 각 픽셀에서 가장 가까운 불투명 픽셀이 어디인지.
    idx = ndimage.distance_transform_edt(~solid, return_distances=False,
                                         return_indices=True)
    rgb = a[..., :3][tuple(idx)]
    out = np.where(solid[..., None], a[..., :3], rgb)
    res = np.concatenate([out, al[..., None]], axis=2)
    return Image.fromarray((res * 255).astype("uint8"), "RGBA")


def pieces(path, min_px=800, close=9):
    """조각마다 (상자, 그림). 자기 덩어리만 남깁니다(RULES 12)."""
    im = Image.open(path).convert("RGBA")
    al = np.asarray(im).astype(float)[..., 3] / 255
    solid = ndimage.binary_fill_holes(
        ndimage.binary_closing(al > .5, np.ones((close, close))))
    lab, k = ndimage.label(solid)
    out = []
    for c in range(1, k + 1):
        own = lab == c
        if own.sum() < min_px:
            continue
        ys, xs = np.nonzero(own)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        arr = np.asarray(im.crop(box)).astype(float)
        arr[..., 3] *= own[box[1]:box[3], box[0]:box[2]]
        out.append((box, Image.fromarray(arr.astype("uint8"), "RGBA")))
    out.sort(key=lambda p: (p[0][1] // 300, p[0][0]))
    return out


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "sheets/furniture_art.png"
    clean(Image.open(src)).save(src.replace(".png", "_clean.png"))
    print(src.replace(".png", "_clean.png"))
