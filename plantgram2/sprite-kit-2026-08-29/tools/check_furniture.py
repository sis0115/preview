"""돌아온 가구 그림을 잘라 놓고, 부탁한 것과 맞는지 봅니다.

합격 기준은 두 가지입니다(RULES 4).
  · 크기  - 두 시트에 함께 그린 긴 화단으로 축척을 맞출 수 있는가
  · 내용  - 가구가 **비어 있는가**. 식물이 그려져 들어오면 우리가 자리에
            심을 수 없습니다. 판 위에 이미 화분이 붙어 있으면 그건 그릇이
            아니라 그림입니다.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, "tools")
from grade_kit import load as load_grades      # noqa: E402

FONT = "../app-kit/assets/fonts/{}.otf"
INK, DIM, RED, OK = (34, 40, 44), (120, 130, 138), (196, 62, 48), (38, 122, 78)


def font(s, b=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if b else "Pretendard-Regular"), s)


def pieces(path, min_px=800):
    im = Image.open(path).convert("RGBA")
    al = np.asarray(im).astype(float)[..., 3] / 255
    solid = ndimage.binary_fill_holes(
        ndimage.binary_closing(al > .5, np.ones((9, 9))))
    lab, k = ndimage.label(solid)
    out = []
    for c in range(1, k + 1):
        own = lab == c
        if own.sum() < min_px:
            continue
        ys, xs = np.nonzero(own)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        a = np.asarray(im.crop(box)).astype(float)
        a[..., 3] *= own[box[1]:box[3], box[0]:box[2]]
        out.append((box, Image.fromarray(a.astype("uint8"), "RGBA")))
    # 왼→오, 위→아래
    out.sort(key=lambda p: (p[0][1] // 300, p[0][0]))
    return out


def main(path="sheets/furniture_art.png", out="sheets/furniture_check.png"):
    got = pieces(path)
    ref, _ = load_grades()
    bed_ref = ref["bed_long"]["art"].width       # 지난 시트의 긴 화단

    # 돌아온 것 중 가장 오른쪽 아래가 화단입니다(2x2 로 다시 배치돼 왔습니다).
    bed = max(got, key=lambda p: p[1].width / max(p[1].height, 1))
    unit = bed_ref / bed[1].width
    labels = ["선반 · 2층", "작업대", "야자", "긴 화단"]
    want = ["비어 있어야 함", "비어 있어야 함", "화분 없이 잎과 줄기만",
            "지난번과 같은 크기"]

    W = 1520
    im = Image.new("RGBA", (W, 760), (244, 243, 239, 255))
    d = ImageDraw.Draw(im)
    d.text((40, 30), "돌아온 가구 그림을 잘라 본 것", font=font(32, True), fill=INK)
    d.text((40, 74), f"긴 화단으로 잰 축척 {unit:.3f} · "
                     f"이 값을 곱하면 지난 시트와 같은 크기가 됩니다",
           font=font(17), fill=DIM)

    x = 40
    for (box, art), name, note in zip(got, labels, want):
        k = unit * .9
        a = art.resize((max(1, round(art.width * k)), max(1, round(art.height * k))),
                       Image.LANCZOS)
        im.alpha_composite(a, (x, 420 - a.height))
        d.text((x, 440), name, font=font(19, True), fill=INK)
        d.text((x, 468), f"{box[2]-box[0]} × {box[3]-box[1]} px "
                         f"→ {round((box[2]-box[0])*unit)} × "
                         f"{round((box[3]-box[1])*unit)}",
               font=font(14), fill=DIM)
        d.text((x, 492), "부탁: " + note, font=font(14), fill=DIM)
        x += max(a.width, 260) + 34

    im.convert("RGB").save(out)
    print(f"{out} · 조각 {len(got)}개 · 축척 {unit:.3f}")
    for (box, art), name in zip(got, labels):
        print(f"  {name:12s} {box[2]-box[0]:4d}x{box[3]-box[1]:4d}"
              f"  → {round((box[2]-box[0])*unit):4d}x{round((box[3]-box[1])*unit):4d}")
    print(f"  (지난 시트 긴 화단 {bed_ref}px 기준)")


if __name__ == "__main__":
    main(*sys.argv[1:])
