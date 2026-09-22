"""가구 시험지 — 식물 놓는 자리를 미리 정해서 그려 달라고 합니다.

전략의 3번 시트입니다. 지금까지는 바닥 한 칸에 화분 하나였습니다. 선반과
작업대가 들어오면 **한 물건 안에 여러 자리**가 생깁니다.

자리를 그림에서 찾아내지 않습니다(RULES 4). 우리가 먼저 정해서 초록 십자로
찍어 보내고, 돌아온 그림의 판이 그 십자를 지나가는지만 봅니다.

  · 주황 십자 - 물건이 **바닥에** 닿는 점
  · 초록 십자 - **화분 바닥이 놓이는** 점. 자리마다 등급이 정해져 있습니다.
  · 납작한 마름모 - 화분이 차지할 바닥 넓이. **화분을 그리지 않습니다.**
  · 세로 막대 - 그 자리에 필요한 여유 높이 (화분 + 식물)

처음에는 자리마다 흐린 화분을 깔아 두었는데, 생성기가 그것을 **내용으로
읽고 화분과 식물을 그려서** 보냈습니다. 판 위에 물건이 붙어 오면 그건
그릇이 아니라 그림입니다. 그래서 가구 칸에서는 화분 밑그림을 빼고, 넓이만
납작한 마름모로 알려 줍니다. 다시 그려 받을 조각(야자·화단)에는 밑그림을
그대로 둡니다 - 거기서는 그리는 것이 목적이니까요.

판 사이 간격은 우리가 지어낸 값이 아니라, 이미 가진 조각을 재서 나온
값입니다. 소형은 화분 114 + 식물 117 = 231 이므로 판 사이가 그보다
좁으면 식물이 윗판을 뚫습니다.

    python3 tools/make_furniture_sheet.py
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from grade_kit import load as load_grades         # noqa: E402

W, H = 1536, 1024
FONT = "../app-kit/assets/fonts/{}.otf"
BG, CARD, EDGE = (242, 241, 236), (252, 252, 250), (219, 219, 212)
INK, MUTE = (46, 64, 52), (140, 150, 143)
MARK = (232, 106, 30)          # 바닥에 닿는 점
SLOT = (28, 138, 92)           # 화분이 놓이는 점
BASE = (206, 204, 196)

TOP, BOT, GROUND = 104, 946, 884

# 한 물건 위에서 두 자리를 벌리는 방향. 바닥 격자의 대각선과 같은 기울기라야
# 판 위에 나란히 놓인 것처럼 보입니다. (배경에서 잰 v 축)
LEAN = (0.865, -0.501)

# (id, 이름, 설명, 칸 폭, 자리들, 밑그림으로 깔 조각)
#   자리 = (등급, 옆으로 벌린 거리, 바닥에서 올린 높이)
#
# 야자를 여기 끼워 넣은 이유: 지난 시트에서 못 쓴 조각이 야자 하나뿐인데
# 열한 조각을 통째로 다시 받았다가 한 장을 통째로 버렸습니다(RULES 11.11).
# 고칠 한 조각만, 축척 기준(긴 화단)과 함께 받습니다.
ITEMS = [
    ("shelf_two", "선반 · 2층",
     "지난번 보내 주신 선반 디자인 그대로,\n다만 판 위를 비워서 그려 주세요.",
     344, [("small", -58, 96), ("small", 58, 96),
           ("medium", -70, 352), ("medium", 70, 352)], None),
    ("bench", "작업대",
     "지난번 보내 주신 작업대 디자인 그대로,\n다만 판 위를 비워서 그려 주세요.",
     344, [("sprout", -46, 72), ("sprout", 46, 72),
           ("medium", -70, 268), ("medium", 70, 268)], None),
    ("xlarge", "야자 · 갈래 사이만 넓게",
     "잎과 줄기만. 화분은 빼 주세요.\n지난번에는 회색 화분이 붙어 왔습니다.",
     318, [], "xlarge"),
    ("bed_long", "긴 화단 · 지난번과 똑같이",
     "축척을 맞추는 기준입니다.\n지난 시트와 같은 크기·모양으로 그려 주세요.",
     330, [], "bed_long"),
]
GRADE_NAME = {"sprout": "새싹", "small": "소형", "medium": "중형", "large": "대형"}
PLANT_OF = {"sprout": "sprout", "small": "small", "medium": "medium",
            "large": "large"}


def font(s, b=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if b else "Pretendard-Regular"), s)


def cross(dr, x, y, colour, r=11, w=3):
    dr.line([(x - r, y), (x + r, y)], fill=colour, width=w)
    dr.line([(x, y - r), (x, y + r)], fill=colour, width=w)


def footprint(dr, x, y, w, iso=1.73):
    """화분이 차지할 바닥 넓이. 납작한 마름모라 물건으로 보이지 않습니다."""
    h = w / iso
    dr.polygon([(x, y - h / 2), (x + w / 2, y), (x, y + h / 2), (x - w / 2, y)],
               outline=SLOT)


def ghost(im, art, foot, x, y, a=.30):
    g = art.copy()
    g.putalpha(g.getchannel("A").point(lambda v: round(v * a)))
    im.alpha_composite(g, (round(x - foot[0]), round(y - foot[1])))


def clearance(dr, x, y, need, label):
    """그 자리에 필요한 여유 높이를 세로 막대로."""
    dr.line([(x, y), (x, y - need)], fill=SLOT, width=1)
    for yy in (y, y - need):
        dr.line([(x - 5, yy), (x + 5, yy)], fill=SLOT, width=1)
    dr.text((x + 8, y - need / 2), label, font=font(12), fill=SLOT, anchor="lm")


def main(out="sheets/furniture_sheet.png"):
    piece, unit = load_grades()
    im = Image.new("RGBA", (W, H), BG + (255,))
    dr = ImageDraw.Draw(im)

    dr.text((24, 14), "가구 시험지 2 — 판 위를 비워 주세요",
            font=font(22, True), fill=INK)
    dr.text((24, 44),
            "주황 십자 = 물건이 바닥에 닿는 점        "
            "초록 십자 = 화분이 놓일 점 · 판 윗면이 이 점을 지나가게        "
            "초록 마름모 = 화분이 차지할 넓이        "
            "세로 막대 = 남겨야 할 여유 높이",
            font=font(13), fill=MUTE)
    dr.text((24, 66),
            "※ 선반과 작업대의 판 위에는 아무것도 올리지 마세요 — 화분도 식물도 "
            "연장도. 빈 가구만 그려 주세요. 안내선 · 글자 · 십자 · 마름모 · 막대 · "
            "흐린 밑그림도 결과물에 그리지 마세요.",
            font=font(13), fill=MUTE)

    spec = {"width": W, "height": H, "ground": GROUND, "items": []}
    gap = (W - sum(i[3] for i in ITEMS)) / (len(ITEMS) + 1)
    x = gap
    for pid, name, note, cw, slots, under in ITEMS:
        dr.rounded_rectangle([x, TOP, x + cw, BOT], 14, fill=CARD, outline=EDGE)
        cx = x + cw / 2
        dr.line([(x + 16, GROUND), (x + cw - 16, GROUND)], fill=BASE, width=1)

        for grade, dx, dy in slots:
            p = piece["pot_" + grade]
            sx = cx + dx * LEAN[0]
            sy = GROUND - dy + dx * LEAN[1]
            footprint(dr, sx, sy, p["art"].width * .92)

        for n, (grade, dx, dy) in enumerate(slots, 1):
            sx = cx + dx * LEAN[0]
            sy = GROUND - dy + dx * LEAN[1]
            need = (piece["pot_" + grade]["art"].height
                    + piece[PLANT_OF[grade]]["art"].height)
            # 여유 높이는 **위에 판이 있는 자리에만** 뜻이 있습니다.
            # 맨 윗판은 머리 위가 열려 있으므로 막대를 그리지 않습니다.
            roofed = any(o[2] > dy for o in slots)
            if dx < 0 and roofed:
                clearance(dr, sx - 76, sy, need, f"{round(need)}")
            cross(dr, sx, sy, SLOT)
            dr.text((sx + 15, sy - 9), f"{n} · {GRADE_NAME[grade]}",
                    font=font(14, True), fill=SLOT)

        if under:
            # 다시 그릴 조각은 지난 그림을 깔아 보여 줍니다. 말로 적은 크기는
            # 지켜지지 않았지만, 밑그림이 있던 칸은 0.99 로 맞았습니다.
            u = piece[under]
            if u["kind"] == "식물":
                ghost(im, u["art"], u["anchor"][0], cx, GROUND, .34)
            else:
                # 화단은 다리가 밑면 한가운데보다 아래로 내려옵니다. 크기를
                # 보여 주는 것이 목적이므로 맨 아랫줄을 바닥에 맞춥니다.
                a = u["art"]
                ghost(im, a, (a.width / 2, a.height), cx, GROUND, .34)
        cross(dr, cx, GROUND, MARK)

        dr.text((cx, TOP + 34), name, font=font(19, True), fill=INK, anchor="ms")
        dr.multiline_text((cx, TOP + 48), note, font=font(13), fill=MUTE,
                          anchor="ma", spacing=5, align="center")
        tag = (f"식물 자리 {len(slots)}개 · 판 위는 비우기" if slots
               else "흐린 밑그림과 같은 크기로")
        dr.text((x + 18, BOT - 30), tag,
                font=font(14, True), fill=SLOT if slots else MUTE)

        spec["items"].append({
            "id": pid, "name": name,
            "box": [round(x), TOP, round(x + cw), BOT],
            "foot": [round(cx), GROUND],
            "slots": [{"x": round(cx + dx * LEAN[0]),
                       "y": round(GROUND - dy + dx * LEAN[1]),
                       "grade": g} for g, dx, dy in slots]})
        x += cw + gap

    im.convert("RGB").save(out)
    json.dump(spec, open(out.replace(".png", ".json"), "w"),
              ensure_ascii=False, indent=1)
    print(out, "·", sum(len(i[4]) for i in ITEMS), "자리")


if __name__ == "__main__":
    main(*sys.argv[1:])
