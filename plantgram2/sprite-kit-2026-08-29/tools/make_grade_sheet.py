"""크기 등급 시험지. 화분 다섯과 식물 다섯을 한 장에 담습니다.

한 장 안에서 그린 것끼리는 축척이 저절로 맞으므로, 화분과 식물을 나눠
받으면 안 됩니다.

크기는 칸마다 **흐린 밑그림**으로 알려 줍니다. 말로 적은 픽셀 수는 지켜지지
않았지만, 밑그림이 있던 칸은 0.99 로 맞았습니다.

    python3 tools/make_grade_sheet.py sheets/grade_sheet.png
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from scene_test import load                       # noqa: E402

W, H = 1536, 1024
HEAD = 72
POT_ROW, PLANT_ROW = 336, H - 72 - 336
POT_GY, PLANT_GY = 288, 540
PAD = 34
TILE = 225.0

BG = (242, 241, 236)
CARD = (252, 252, 250)
EDGE = (219, 219, 212)
INK = (46, 64, 52)
MUTE = (140, 150, 143)
MARK = (232, 106, 30)
BASE = (206, 204, 196)
FONT = "../app-kit/assets/fonts/{}.otf"

# (등급, 식물 폭 · 타일 대비, 화분 폭 · 타일 대비)
GRADES = [
    ("새싹", .22, .30),
    ("소형", .45, .45),
    ("중형", .63, .60),
    ("대형", .75, .70),
    ("특대형", 1.00, .92),
]
POT_NOTE = ["아주 작은 것", "선반에 올릴 것", "흔한 크기", "조금 큰 것", "가장 큰 것"]
PLANT_NOTE = ["갓 심은 모종. 떡잎 두어 장",
              "다육이나 작은 관엽",
              "잎이 여러 장 벌어진 관엽",
              "몬스테라 같은 큰 잎",
              "야자처럼 키 큰 나무"]


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def cross(dr, x, y, r=10, w=3):
    dr.line([(x - r, y), (x + r, y)], fill=MARK, width=w)
    dr.line([(x, y - r), (x, y + r)], fill=MARK, width=w)


def bar(dr, cx, y, wid, text):
    dr.line([(cx - wid / 2, y), (cx + wid / 2, y)], fill=MARK, width=2)
    for px, d in ((cx - wid / 2, 1), (cx + wid / 2, -1)):
        dr.line([(px, y), (px + 7 * d, y - 4)], fill=MARK, width=2)
        dr.line([(px, y), (px + 7 * d, y + 4)], fill=MARK, width=2)
    dr.text((cx, y + 20), text, font=font(13, True), fill=MARK, anchor="ms")


def main(out="sheets/grade_sheet.png"):
    piece = load()
    pot = piece["pot_round"]
    im = Image.new("RGBA", (W, H), BG + (255,))
    dr = ImageDraw.Draw(im)

    dr.text((24, 12), "크기 등급 시험지 — 흐린 밑그림과 같은 크기로",
            font=font(21, True), fill=INK)
    dr.text((24, 40),
            "위 다섯 칸은 화분, 아래 다섯 칸은 그 화분에 심을 식물입니다. "
            "칸마다 흐린 밑그림이 크기를 알려 줍니다.        "
            "주황 십자 = 바닥에 닿는 점 / 줄기 밑동        "
            "※ 안내선·글자·흐린 밑그림은 결과물에 그리지 마세요",
            font=font(13), fill=MUTE)

    spec = {"width": W, "height": H, "items": []}

    for row, (kind, gy, rh, note) in enumerate(
            (("화분", POT_GY, POT_ROW, POT_NOTE),
             ("식물", PLANT_GY, PLANT_ROW, PLANT_NOTE))):
        items = list(GRADES)
        if kind == "화분":
            # 이전 시트와 축척을 맞출 기준 조각. 이것 하나가 겹쳐 있어야
            # 새 시트를 이전 것에 맞춰 통째로 줄일 수 있습니다.
            items = items + [("긴 화단", None, None)]
        widths = []
        for g in items:
            if g[1] is None:
                widths.append(piece["bed_long"]["art"].width + PAD * 2)
            else:
                widths.append(round((g[2] if kind == "화분" else g[1]) * TILE)
                              + PAD * 2)
        ox = (W - sum(widths)) / 2
        oy = HEAD + (0 if row == 0 else POT_ROW)
        for n, ((name, pk, potk), cw) in enumerate(zip(items, widths)):
            dr.rounded_rectangle([ox + 5, oy + 5, ox + cw - 5, oy + rh - 5],
                                 12, fill=CARD, outline=EDGE)
            cx = ox + cw / 2
            src = piece["bed_long"] if potk is None else pot
            k = 1.0 if potk is None else potk * TILE / pot["art"].width
            art = src["art"].resize(
                (round(src["art"].width * k), round(src["art"].height * k)),
                Image.LANCZOS)
            art.putalpha(art.getchannel("A").point(lambda v: round(v * .30)))
            fx, fy = src["foot"][0] * k, src["foot"][1] * k
            px, py = round(cx - fx), round(oy + gy - fy)
            im.alpha_composite(art, (px, py))
            dr.line([(ox + 14, oy + gy), (ox + cw - 14, oy + gy)],
                    fill=BASE, width=1)

            if kind == "화분":
                mx, my = cx, oy + gy
                wid = src["art"].width if potk is None else potk * TILE
                tag = f"{round(wid)}px"
            else:
                ax, ay = src["anchor"][0][0] * k, src["anchor"][0][1] * k
                mx, my = px + ax, py + ay
                wid = pk * TILE
                tag = f"{round(wid)}px"
            cross(dr, mx, my)
            # 치수선은 화분 바로 위에. 멀리 떼어 놓으면 무엇의 폭인지
            # 알 수 없습니다.
            bar(dr, cx, py - 30, wid, tag)

            title = name if potk is None else f"{name} {kind}"
            dr.text((ox + 14, oy + 16), title, font=font(16, True), fill=INK)
            dr.text((ox + 14, oy + 40),
                    "지금 것과 같은 크기 — 기준 맞추기" if potk is None else note[n],
                    font=font(11), fill=MUTE)

            spec["items"].append({
                "id": ("bed_long" if potk is None else
                       f"{'pot' if kind == '화분' else 'plant'}_{n}"),
                "kind": kind, "grade": name, "cell": len(spec["items"]),
                "box": [round(ox), oy, round(ox + cw), oy + rh],
                "ground": [round(mx), round(my)], "width": round(wid)})
            ox += cw

    im.convert("RGB").save(out)
    json.dump(spec, open(out.replace(".png", ".json"), "w"),
              indent=1, ensure_ascii=False)
    for it in spec["items"]:
        print(f"  {it['grade']:5} {it['kind']}  {it['width']:4}px")
    print(f"{out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
