"""빛 번짐이 깔린 시트에서 조각을 오려 냅니다.

색으로는 나눌 수 없습니다 - 번짐이 조각 색 그대로 바깥까지 이어져서,
화분 바깥 빈 곳과 화분 몸통의 차이가 255 중 13 밖에 안 됩니다.

대신 **매끈함**으로 나눕니다. 번짐은 어느 자리에서 봐도 매끈합니다.
조각 안에는 테두리·무늬·그늘이 있어 기울기가 섭니다. 기울기가 선 곳을
모아 닫으면 조각의 겉모양이 나옵니다.

다만 이 방법은 **겉모양만** 얻습니다. 잎과 잎 사이처럼 안쪽에 뚫린 틈은
메워집니다. 그래서 화분에는 쓰고 식물에는 쓰지 않습니다.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def edges(path, hi=96, lo=85, close=9):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255
    lum = ndimage.gaussian_filter(a.mean(2), 1.2)
    gy, gx = np.gradient(lum)
    g = np.hypot(gx, gy)
    # 약한 선만 있는 곳은 번짐의 잔물결입니다. 강한 선에서 이어진 것만 남깁니다.
    strong = g > np.percentile(g, hi)
    weak = g > np.percentile(g, lo)
    e = ndimage.binary_propagation(strong, mask=weak)
    return a, ndimage.binary_fill_holes(
        ndimage.binary_closing(e, np.ones((close, close))))


def keyed(path, min_px=400):
    """grade_kit.keyed 와 같은 것을 돌려줍니다: (RGBA, 남길 마스크, 라벨)."""
    a, solid = edges(path)
    lab, k = ndimage.label(solid)
    sz = ndimage.sum(solid, lab, range(1, k + 1))
    keep = np.isin(lab, [i + 1 for i in range(k) if sz[i] >= min_px])

    # 번짐은 조각과 **같은 색**입니다. 그래서 가장자리에 섞여 들어온 색도
    # 조각 색이라 흰 테가 지지 않습니다. 색은 손대지 않고 알파만 만듭니다.
    # 다만 경계를 한 픽셀 안으로 당겨야 번짐이 테두리로 남지 않습니다.
    inner = ndimage.binary_erosion(keep, np.ones((3, 3)))
    alpha = np.clip(ndimage.gaussian_filter(inner.astype(float), .8) * 1.25, 0, 1)
    alpha = np.where(keep, alpha, 0)

    out = Image.fromarray((a * 255).astype("uint8"), "RGB").convert("RGBA")
    out.putalpha(Image.fromarray((alpha * 255).astype("uint8")))
    return out, keep, lab


if __name__ == "__main__":
    im, keep, lab = keyed(sys.argv[1] if len(sys.argv) > 1
                          else "sheets/grade_art2.png")
    im.save("sheets/grade_art2_keyed.png")
    print("sheets/grade_art2_keyed.png")
