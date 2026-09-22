"""그릇마다 자리를 꽉 채워 바닥 위에 놓아 봅니다.

앱이 그리는 차례 그대로 - 그림자, 그릇, 그리고 자리마다 (판 위면)화분과
식물. 눈으로 볼 수 있어야 틀린 것이 보입니다.
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

A = "../app-kit/assets"
FONT = "../app-kit/assets/fonts/{}.otf"


def font(s, b=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if b else "Pretendard-Regular"), s)


def main(out="sheets/slot_check.png"):
    cat = json.load(open(f"{A}/catalog.json", encoding="utf-8"))
    g = cat["grid"]
    S = g["unitScale"]
    stage = Image.open(f"{A}/greenhouse/stage.png").convert("RGBA")

    def art(path, k=S):
        im = Image.open(path).convert("RGBA")
        return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                         Image.LANCZOS)

    ids = [k for k, v in cat["pots"].items() if v["slots"]]
    cell = 420
    cols = 4
    rows = (len(ids) + cols - 1) // cols
    im = Image.new("RGBA", (cell * cols, (cell + 46) * rows), (244, 243, 239, 255))
    d0 = ImageDraw.Draw(im)

    for n, pid in enumerate(ids):
        pot = cat["pots"][pid]
        card = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        # 바닥 한 조각을 배경으로 (격자 눈금이 보이게)
        card.alpha_composite(stage.crop((620, 560, 620 + cell, 560 + cell)))
        cx, cy = cell / 2, cell * .68

        sh = pot["shadow"]
        card.alpha_composite(art(f"{A}/shadows/{pid}.png"),
                             (round(cx - sh["anchorX"] * S),
                              round(cy - sh["anchorY"] * S + sh["drop"] * S)))
        card.alpha_composite(art(f"{A}/pots/{pid}.png"),
                             (round(cx - pot["foot"]["x"] * S),
                              round(cy - pot["foot"]["y"] * S)))

        dr = ImageDraw.Draw(card)
        for k, s in enumerate(sorted(pot["slots"], key=lambda q: q["y"]), 1):
            grade = s["grades"][-1]
            pl = cat["plants"][grade]
            bx = cx + (s["x"] - pot["foot"]["x"]) * S
            by = cy + (s["y"] - pot["foot"]["y"]) * S
            if s["potted"]:
                inner = cat["pots"][pl["pot"]]
                card.alpha_composite(art(f"{A}/pots/{pl['pot']}.png"),
                                     (round(bx - inner["foot"]["x"] * S),
                                      round(by - inner["foot"]["y"] * S)))
                bx += (inner["slots"][0]["x"] - inner["foot"]["x"]) * S
                by += (inner["slots"][0]["y"] - inner["foot"]["y"]) * S
            card.alpha_composite(art(f"{A}/plants/{grade}.png"),
                                 (round(bx - pl["stemX"] * S),
                                  round(by - pl["stemY"] * S)))
            dr.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(210, 60, 40, 255))

        x, y = (n % cols) * cell, (n // cols) * (cell + 46)
        im.alpha_composite(card, (x, y))
        d0.text((x + 12, y + cell + 10),
                f"{cat['names'][pid]} · {pot['cells'][0]}x{pot['cells'][1]}칸 · "
                f"자리 {len(pot['slots'])} · "
                f"{'화분째' if pot['slots'][0]['potted'] else '흙에'}",
                font=font(16, True), fill=(34, 40, 44))

    im.convert("RGB").save(out)
    print(out, "·", len(ids), "그릇")


if __name__ == "__main__":
    main(*sys.argv[1:])
