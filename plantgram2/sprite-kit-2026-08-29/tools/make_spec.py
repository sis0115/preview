"""조합만 보는 시험지를 그립니다. 크기는 정하지 않습니다.

크기를 맞추려다 정작 조합을 놓쳤습니다. 밑면 마름모, 치수선, 좌우 한계,
크기 보기까지 얹으면서 "칸을 채워라"는 말이 되어 버렸고, 그러는 사이 줄기가
화분 가운데에서 밀려도 눈치채지 못했습니다.

조합에 필요한 것은 **닿는 점 하나**입니다.

    화분 : 바닥에 닿는 자리
    식물 : 줄기 밑동

이 두 점을 겹치면 심은 것처럼 보입니다. 크기는 한 장 안에서 그린 것끼리
저절로 맞으므로, 무대에 얹을 때 시트 전체를 한 배율로 줄이면 됩니다 -
조각 하나만 늘리는 것이 아니라 전부 같은 값으로.

    python3 tools/make_spec.py sheets/spec_04.png
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1536, 1024
HEAD = 68
COLS, ROWS = 4, 2
CW, CH = W // COLS, (H - HEAD) // ROWS      # 384 x 478
GX, GY = CW // 2, 372                       # 칸 안에서 닿는 점

BG = (242, 241, 236)
CARD = (252, 252, 250)
EDGE = (219, 219, 212)
INK = (46, 64, 52)
MUTE = (140, 150, 143)
MARK = (232, 106, 30)
BASE = (208, 205, 196)

FONT = "../app-kit/assets/fonts/{}.otf"

ITEMS = [
    dict(id="pot_round", kind="화분", name="둥근 화분",
         note="테라코타. 흙이 위에서 잘 보이게"),
    dict(id="bed_long", kind="화분", name="긴 화단",
         note="나무. 흙이 두 곳으로 나뉘어 보이게"),
    dict(id="planter_big", kind="화분", name="큰 화분",
         note="묵직한 석재. 큰 나무 한 그루용"),
    dict(id="shelf", kind="가구", name="선반",
         note="나무 2단. 판이 수평으로 보이게"),
    dict(id="plant_s", kind="식물", name="작은 식물",
         note="선반에 올릴 만한 것"),
    dict(id="plant_m", kind="식물", name="식물",
         note="몬스테라 같은 관엽"),
    dict(id="plant_tall", kind="식물", name="키 큰 식물",
         note="대나무처럼 위로 자라는 것"),
    dict(id="plant_big", kind="식물", name="특대형 식물",
         note="야자처럼 큰 나무"),
]


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def cross(dr, x, y, r=11, width=3):
    dr.line([(x - r, y), (x + r, y)], fill=MARK, width=width)
    dr.line([(x, y - r), (x, y + r)], fill=MARK, width=width)


def draw_cell(dr, ox, oy, n, it):
    dr.rounded_rectangle([ox + 6, oy + 6, ox + CW - 6, oy + CH - 6], 14,
                         fill=CARD, outline=EDGE)
    dr.text((ox + 18, oy + 16), f"{n}. {it['name']}", font=font(19, True), fill=INK)
    dr.text((ox + 18, oy + 42), it["note"], font=font(13), fill=MUTE)

    gx, gy = ox + GX, oy + GY

    # 바닥선. 여덟 칸이 같은 높이에 서 있다는 표시입니다.
    dr.line([(ox + 16, gy), (ox + CW - 16, gy)], fill=BASE, width=1)
    # 닿는 자국. 크기 표시가 아니라 "여기가 바닥"이라는 뜻입니다.
    dr.ellipse([gx - 46, gy - 15, gx + 46, gy + 15], outline=BASE, width=2)
    cross(dr, gx, gy)

    tag = "줄기 밑동이 여기에" if it["kind"] == "식물" else "바닥이 여기에 닿게"
    dr.text((gx, gy + 34), tag, font=font(13, True), fill=MARK, anchor="ms")
    dr.text((gx, oy + CH - 22), "크기는 자유", font=font(12), fill=MUTE, anchor="ms")


def main(out="sheets/spec_04.png"):
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)

    dr.text((24, 12), "조합 시험지 — 닿는 점만 맞춰 주세요",
            font=font(21, True), fill=INK)
    dr.text((24, 40),
            "크기는 정하지 않습니다. 자연스럽게 그려 주세요.        "
            "주황 십자 = 바닥에 닿는 점 · 회색 선 = 여덟 칸이 서 있는 높이        "
            "※ 안내선과 글자는 결과물에 그리지 마세요",
            font=font(13), fill=MUTE)

    spec = {"width": W, "height": H, "items": []}
    for n, it in enumerate(ITEMS):
        ox = (n % COLS) * CW
        oy = HEAD + (n // COLS) * CH
        draw_cell(dr, ox, oy, n + 1, it)
        spec["items"].append({
            "id": it["id"], "kind": it["kind"], "cell": n,
            "box": [ox, oy, ox + CW, oy + CH],
            "ground": [ox + GX, oy + GY],
        })

    im.save(out)
    json.dump(spec, open(out.replace(".png", ".json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"{out} · {len(ITEMS)}칸 · 닿는 점만 표시, 크기 제한 없음")


if __name__ == "__main__":
    main(*sys.argv[1:])
