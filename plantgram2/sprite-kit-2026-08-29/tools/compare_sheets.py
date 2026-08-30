"""두 시트에서 같은 조각을 꺼내 나란히 놓고 봅니다.

어느 쪽을 쓸지는 눈으로 정할 문제가 아니라 잘라 본 결과로 정합니다.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, "tools")
import deglow                                  # noqa: E402
from grade_kit import keyed as keyed_checker    # noqa: E402

FONT = "../app-kit/assets/fonts/{}.otf"
INK, DIM = (34, 40, 44), (120, 130, 138)


def font(s, b=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if b else "Pretendard-Regular"), s)


def pieces(im, keep, lab, row):
    """한 줄에서 왼쪽부터 조각을 꺼냅니다. 자기 덩어리만 남깁니다(RULES 12)."""
    out = []
    for c in np.unique(lab[keep]):
        own = (lab == c) & keep
        ys, xs = np.nonzero(own)
        if len(xs) < 400:
            continue
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        mid = (box[1] + box[3]) / 2
        if (mid < 500) != (row == "top"):
            continue
        art = im.crop(box).copy()
        a = np.asarray(art).astype(float)
        a[..., 3] *= own[box[1]:box[3], box[0]:box[2]]
        out.append((box, Image.fromarray(a.astype("uint8"), "RGBA")))
    out.sort(key=lambda p: p[0][0])
    return out


def strip(items, w, h, y0, im, d, label):
    d.text((40, y0 - 34), label, font=font(22, True), fill=INK)
    x = 40
    for box, art in items:
        k = min(1.0, (h - 40) / art.height, 240 / art.width)
        a = art.resize((max(1, round(art.width * k)), max(1, round(art.height * k))),
                       Image.LANCZOS)
        im.alpha_composite(a, (x, y0 + h - 30 - a.height))
        d.text((x, y0 + h - 24), f"{box[2]-box[0]}px", font=font(15), fill=DIM)
        x += a.width + 26
    return x


def main():
    W = 1560
    im = Image.new("RGBA", (W, 1180), (244, 243, 239, 255))
    d = ImageDraw.Draw(im)
    d.text((40, 30), "같은 조각, 두 시트", font=font(34, True), fill=INK)
    d.text((40, 76), "위 = 새로 받은 시트(번짐)를 기울기로 오린 것 · "
                     "아래 = 지난 시트(체커보드)를 색으로 오린 것",
           font=font(18), fill=DIM)

    n_im, n_keep, n_lab = deglow.keyed("sheets/grade_art2.png")
    o_im, o_keep, o_lab = keyed_checker("sheets/grade_art.png")

    y = 140
    for row, title in (("top", "화분"), ("bot", "식물")):
        strip(pieces(n_im, n_keep, n_lab, row), W, 240, y,
              im, d, f"{title} · 새 시트")
        y += 270
        strip(pieces(o_im, o_keep, o_lab, row), W, 240, y,
              im, d, f"{title} · 지난 시트")
        y += 300

    im.convert("RGB").save("sheets/sheet_compare.png")
    print("sheets/sheet_compare.png")


if __name__ == "__main__":
    main()
