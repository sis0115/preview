"""가구 시험지 — 식물 놓는 자리를 미리 정해서 그려 달라고 합니다.

전략의 3번 시트입니다. 지금까지는 바닥 한 칸에 화분 하나였습니다. 선반과
작업대가 들어오면 **한 물건 안에 여러 자리**가 생깁니다.

자리를 그림에서 찾아내지 않습니다(RULES 4). 우리가 먼저 정해서 초록 십자로
찍어 보내고, 돌아온 그림의 판이 그 십자를 지나가는지만 봅니다.

  · 주황 십자 - 물건이 **바닥에** 닿는 점
  · 초록 십자 - **화분 바닥이 놓이는** 점. 자리마다 등급이 정해져 있습니다.
  · 흐린 화분 - 그 자리에 실제로 올라갈 화분
  · 세로 막대 - 그 자리에 필요한 여유 높이 (화분 + 식물)

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

# (id, 이름, 설명, 칸 폭, 자리들)
#   자리 = (등급, 옆으로 벌린 거리, 바닥에서 올린 높이)
ITEMS = [
    ("shelf_two", "선반 · 2층",
     "다리 넷에 판 두 장. 아래 판과 맨 위 판이\n각각 초록 십자를 지나가야 합니다.",
     392, [("small", -58, 96), ("small", 58, 96),
           ("medium", -70, 352), ("medium", 70, 352)]),
    ("bench", "작업대",
     "상판 하나와 그 아래 낮은 판 하나.\n흙자루·모종삽을 곁들여도 좋습니다.",
     392, [("sprout", -46, 72), ("sprout", 46, 72),
           ("medium", -70, 268), ("medium", 70, 268)]),
    ("stand", "받침대",
     "굵은 화분 하나를 올리는\n낮고 튼튼한 받침.",
     288, [("large", 0, 128)]),
    ("bed_long", "긴 화단 · 지난번과 똑같이",
     "축척을 맞추는 기준입니다.\n지난 시트와 같은 크기·모양으로 그려 주세요.",
     340, []),
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

    dr.text((24, 14), "가구 시험지 — 식물 놓는 자리를 정해서 보냅니다",
            font=font(22, True), fill=INK)
    dr.text((24, 44),
            "주황 십자 = 물건이 바닥에 닿는 점        "
            "초록 십자 = 화분 바닥이 놓이는 점 · 판이 이 점을 지나가게        "
            "흐린 화분 = 그 자리에 올라갈 화분        "
            "세로 막대 = 남겨야 할 여유 높이",
            font=font(13), fill=MUTE)
    dr.text((24, 66),
            "※ 안내선 · 글자 · 십자 · 막대 · 흐린 밑그림은 결과물에 그리지 마세요. "
            "네 물건 모두 같은 각도 · 같은 축척 · 배경은 순수 마젠타 #FF00FF 단색.",
            font=font(13), fill=MUTE)

    spec = {"width": W, "height": H, "ground": GROUND, "items": []}
    gap = (W - sum(i[3] for i in ITEMS)) / (len(ITEMS) + 1)
    x = gap
    for pid, name, note, cw, slots in ITEMS:
        dr.rounded_rectangle([x, TOP, x + cw, BOT], 14, fill=CARD, outline=EDGE)
        cx = x + cw / 2
        dr.line([(x + 16, GROUND), (x + cw - 16, GROUND)], fill=BASE, width=1)

        # 뒤쪽(위) 자리부터 깔아야 앞 화분이 위에 옵니다.
        put = sorted(slots, key=lambda s: -s[2])
        for grade, dx, dy in put:
            p = piece["pot_" + grade]
            sx = cx + dx * LEAN[0]
            sy = GROUND - dy + dx * LEAN[1]
            ghost(im, p["art"], p["foot"], sx, sy)

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

        if pid == "bed_long":
            # 화단은 다리가 밑면 한가운데보다 아래로 내려옵니다. 기준 조각은
            # 크기를 보여 주는 것이 목적이므로 맨 아랫줄을 바닥에 맞춥니다.
            b = piece["bed_long"]["art"]
            ghost(im, b, (b.width / 2, b.height), cx, GROUND, .34)
        cross(dr, cx, GROUND, MARK)

        dr.text((cx, TOP + 34), name, font=font(19, True), fill=INK, anchor="ms")
        dr.multiline_text((cx, TOP + 48), note, font=font(13), fill=MUTE,
                          anchor="ma", spacing=5, align="center")
        dr.text((x + 18, BOT - 30),
                f"식물 자리 {len(slots)}개" if slots else "자리 없음 · 기준 조각",
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
