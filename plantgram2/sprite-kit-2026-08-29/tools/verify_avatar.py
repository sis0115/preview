"""받은 아바타 시트를 기준 그림의 칸대로 잘라, 실제로 겹쳐 봅니다.

기준점을 찾을 필요가 없습니다. 우리가 그려 보낸 자리가 곧 기준점이라
avatar_ref.json 에 이미 적혀 있습니다. 화분의 흙 자리와 식물의 밑동
자리를 맞춰 놓고 눈으로 확인합니다.

    python3 tools/verify_avatar.py sheets/avatar.png
"""
import json, os, sys
from PIL import Image, ImageDraw


def cell_box(n, m):
    r, c = divmod(n, m["cols"])
    return (c * m["cellW"], r * m["cellH"],
            (c + 1) * m["cellW"], (r + 1) * m["cellH"])


def cut(sheet, n, m):
    """칸 하나를 오리고, 그 안에서의 기준점 좌표도 함께 돌려줍니다."""
    box = cell_box(n, m)
    return sheet.crop(box), box[0], box[1]


def main(path, ref="sheets/avatar_ref.json", out="sheets/avatar_check.png"):
    m = json.load(open(ref))
    sheet = Image.open(path).convert("RGBA")
    if sheet.size != (m["cellW"] * m["cols"], m["cellH"] * m["rows"]):
        sheet = sheet.resize(
            (m["cellW"] * m["cols"], m["cellH"] * m["rows"]), Image.LANCZOS)
        print(f"크기를 {sheet.size} 로 맞췄습니다")

    pots = {p["id"]: p for p in m["pots"]}
    plants = {p["id"]: p for p in m["plants"]}

    # 화분마다 식물 하나씩 얹어 봅니다. 긴 화단은 같은 식물 두 그루.
    pairs = list(zip(pots.values(), list(plants.values()) * 2))
    cols = 4
    rows = (len(pairs) + cols - 1) // cols
    cw, ch = m["cellW"], m["cellH"] * 2
    canvas = Image.new("RGB", (cols * cw, rows * ch), (247, 246, 242))
    dr = ImageDraw.Draw(canvas)

    for n, (pot, plant) in enumerate(pairs):
        r, c = divmod(n, cols)
        ox, oy = c * cw, r * ch
        pot_img, pox, poy = cut(sheet, pot["cell"], m)
        plant_img, qox, qoy = cut(sheet, plant["cell"], m)

        # 화분을 칸 그대로 놓고, 식물 밑동을 흙 자리에 맞춥니다.
        base = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        py = ch - m["cellH"]
        base.alpha_composite(pot_img, (0, py))
        for slot in pot["slots"]:
            sx, sy = slot["x"] - pox, slot["y"] - poy      # 칸 안에서의 흙 자리
            bx, by = plant["x"] - qox, plant["y"] - qoy    # 칸 안에서의 밑동
            base.alpha_composite(plant_img, (round(sx - bx), round(py + sy - by)))
        canvas.paste(base, (ox, oy), base)
        dr.text((ox + 8, oy + 6), f'{pot["id"]} + {plant["id"]}', fill=(90, 90, 86))

    canvas.save(out)
    print(f"{out}  조합 {len(pairs)}개 — 밑동이 흙에 닿았는지 보세요")


if __name__ == "__main__":
    main(*sys.argv[1:])
