"""조각의 밑면이 정말 그 칸들 위에 있는지 겹쳐서 봅니다.

칸 수만 맞고 **방향**이 틀리면 조각은 한쪽으로 삐져나가고 반대쪽 칸은
빈 채로 잡힙니다. 눈으로 볼 수 있게 덮는 칸을 칠해 얹습니다.
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

A = "../app-kit/assets"
FONT = "../app-kit/assets/fonts/{}.otf"


def font(s, b=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if b else "Pretendard-Regular"), s)


def main(out="sheets/cells_check.png"):
    cat = json.load(open(f"{A}/catalog.json", encoding="utf-8"))
    g = cat["grid"]
    T = np.array([g["topX"], g["topY"]])
    U = np.array([g["uX"], g["uY"]])
    V = np.array([g["vX"], g["vY"]])
    S = g["unitScale"]

    def corner(i, j):
        return T + U * i + V * j

    def centre(i, j):
        return T + U * (i + .5) + V * (j + .5)

    stage = Image.open(f"{A}/greenhouse/stage.png").convert("RGBA")

    # 두 방향을 한 장에 — 같은 조각, 같은 칸, 방향만 다르게
    show = [("bed_long", 3, 3), ("shelf_planted", 3, 3), ("bench_planted", 3, 3)]
    W = 520
    im = Image.new("RGBA", (W * len(show), 720), (244, 243, 239, 255))
    d0 = ImageDraw.Draw(im)

    for n, (pid, ci, cj) in enumerate(show):
        pot = cat["pots"][pid]
        a, b = pot.get("cells", [1, 1])
        for r, (rot, tag) in enumerate([(0, "rot 0 · 오른쪽 위로"),
                                        (1, "rot 1 · 왼쪽 위로")]):
            cells = [(a, b), (b, a)][rot]
            cov = [(ci - di, cj - dj)
                   for di in range(cells[0]) for dj in range(cells[1])]
            sc = stage.copy()
            dr = ImageDraw.Draw(sc, "RGBA")
            for (i, j) in cov:
                dr.polygon([tuple(corner(i, j)), tuple(corner(i + 1, j)),
                            tuple(corner(i + 1, j + 1)), tuple(corner(i, j + 1))],
                           fill=(210, 70, 40, 90), outline=(210, 70, 40, 255))
            anc = np.mean([centre(i, j) for (i, j) in cov], axis=0)

            art = Image.open(f"{A}/pots/{pid}.png").convert("RGBA")
            art = art.resize((round(art.width * S), round(art.height * S)),
                             Image.LANCZOS)
            fx, fy = pot["foot"]["x"] * S, pot["foot"]["y"] * S
            if rot:
                art = art.transpose(Image.FLIP_LEFT_RIGHT)
                fx = art.width - fx
            sc.alpha_composite(art, (round(anc[0] - fx), round(anc[1] - fy)))

            box = (round(anc[0]) - 230, round(anc[1]) - 250,
                   round(anc[0]) + 230, round(anc[1]) + 110)
            im.alpha_composite(sc.crop(box), (n * W + 30, 60 + r * 360))
            d0.text((n * W + 30, 40 + r * 360),
                    f"{pid} · {tag} · {cells[0]}x{cells[1]}",
                    font=font(15, True), fill=(34, 40, 44))

    im.convert("RGB").save(out)
    print(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
