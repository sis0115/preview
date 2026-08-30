"""크기 등급 시험지. 기준을 픽셀이 아니라 **화분**에 붙입니다.

"폭 240px" 이라고 적어 봤자 지켜지지 않았습니다. 대신 그 식물이 심길 화분을
칸마다 흐리게 깔아 둡니다 - "이 화분에 심을 크기" 는 눈으로 바로 보입니다.
크기를 늘리라는 뜻이 아니라 견줄 것을 주는 것입니다.

등급은 이미 잰 값에서 나왔습니다.
  · 긴 화단 심는 자리 간격 108px → 두 그루가 안 겹치려면 한 그루 ≤ 100px
  · 선반 폭 277px → 화분 둘을 올리면 하나 ≤ 130px
  · 표준 화분 180px · 큰 화분 334px

    python3 tools/make_size_sheet.py sheets/size_sheet.png
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from scene_test import load                       # noqa: E402

W, H = 1536, 1024
HEAD = 68
SMALL_W, SMALL_H = 260, 478                       # 왼쪽 3열 x 2행
TALL_W = 378                                      # 오른쪽 2열, 통칸
SMALL_GY, TALL_GY = 392, 848                      # 칸 안에서 바닥

BG = (242, 241, 236)
CARD = (252, 252, 250)
EDGE = (219, 219, 212)
INK = (46, 64, 52)
MUTE = (140, 150, 143)
MARK = (232, 106, 30)
BASE = (206, 204, 196)

FONT = "../app-kit/assets/fonts/{}.otf"

ITEMS = [
    dict(id="pot_small", kind="화분", name="작은 화분",
         ghost="pot_round", slot=None, tall=False,
         note="흐린 화분의 절반쯤. 선반에 올릴 것"),
    dict(id="sprout", kind="식물", name="새싹",
         ghost="pot_round", slot=0, tall=False,
         note="갓 심은 모종. 흙 위로 조금만"),
    dict(id="small_a", kind="식물", name="소형",
         ghost="pot_round", slot=0, tall=False,
         note="흐린 화분 폭의 절반쯤. 화단에 두 그루 심어도 안 겹치게"),
    dict(id="medium_a", kind="식물", name="중형",
         ghost="pot_round", slot=0, tall=False,
         note="흐린 화분에 알맞은 크기"),
    dict(id="small_b", kind="식물", name="소형 · 다른 종",
         ghost="pot_round", slot=0, tall=False,
         note="위 소형과 같은 크기, 다른 잎"),
    dict(id="medium_b", kind="식물", name="중형 · 다른 종",
         ghost="pot_round", slot=0, tall=False,
         note="위 중형과 같은 크기, 다른 잎"),
    dict(id="large", kind="식물", name="대형",
         ghost="planter_big", slot=0, tall=True,
         note="흐린 큰 화분에 알맞은 크기"),
    dict(id="xlarge", kind="식물", name="특대형",
         ghost="planter_big", slot=0, tall=True,
         note="흐린 큰 화분에 꽉 차는 크기. 키 큰 나무"),
]


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def cross(dr, x, y, r=11, w=3):
    dr.line([(x - r, y), (x + r, y)], fill=MARK, width=w)
    dr.line([(x, y - r), (x, y + r)], fill=MARK, width=w)


def main(out="sheets/size_sheet.png"):
    piece = load()
    im = Image.new("RGBA", (W, H), BG + (255,))
    dr = ImageDraw.Draw(im)

    dr.text((24, 12), "크기 등급 시험지 — 흐린 화분에 견주어 그려 주세요",
            font=font(21, True), fill=INK)
    dr.text((24, 40),
            "칸마다 그 식물이 심길 화분이 흐리게 깔려 있습니다. "
            "그 화분에 심었을 때 자연스러운 크기로 그려 주세요.        "
            "주황 십자 = 줄기 밑동이 놓일 점        "
            "※ 안내선·글자·흐린 화분은 결과물에 그리지 마세요",
            font=font(13), fill=MUTE)

    boxes = []
    for n, it in enumerate(ITEMS):
        if not it["tall"]:
            col, row = n % 3, n // 3
            ox, oy = col * SMALL_W, HEAD + row * SMALL_H
            cw, ch, gy = SMALL_W, SMALL_H, SMALL_GY
        else:
            ox = 3 * SMALL_W + (n - 6) * TALL_W
            oy, cw, ch, gy = HEAD, TALL_W, H - HEAD, TALL_GY
        boxes.append((ox, oy, cw, ch, gy))

    spec = {"width": W, "height": H, "items": []}
    for n, (it, (ox, oy, cw, ch, gy)) in enumerate(zip(ITEMS, boxes)):
        dr.rounded_rectangle([ox + 6, oy + 6, ox + cw - 6, oy + ch - 6], 14,
                             fill=CARD, outline=EDGE)
        dr.text((ox + 16, oy + 14), f"{n + 1}. {it['name']}",
                font=font(18, True), fill=INK)
        for k, line in enumerate(it["note"].split(". ")):
            dr.text((ox + 16, oy + 40 + k * 17), line, font=font(12), fill=MUTE)

        g = piece[it["ghost"]]
        art = g["art"].copy()
        art.putalpha(art.getchannel("A").point(lambda v: round(v * .30)))
        fx, fy = g["foot"]
        px, py = round(ox + cw / 2 - fx), round(oy + gy - fy)
        im.alpha_composite(art, (px, py))

        dr.line([(ox + 16, oy + gy), (ox + cw - 16, oy + gy)], fill=BASE, width=1)

        if it["slot"] is None:                      # 화분 칸 - 바닥에 닿는 점
            mx, my = ox + cw / 2, oy + gy
            tag = "바닥이 여기에 닿게"
        else:
            ax, ay = g["anchor"][it["slot"]]
            mx, my = px + ax, py + ay
            tag = "줄기 밑동이 여기에"
        cross(dr, mx, my)
        dr.text((mx, my + 30), tag, font=font(12, True), fill=MARK, anchor="ms")

        spec["items"].append({"id": it["id"], "kind": it["kind"], "cell": n,
                              "box": [ox, oy, ox + cw, oy + ch],
                              "ground": [round(mx), round(my)]})

    im.convert("RGB").save(out)
    json.dump(spec, open(out.replace(".png", ".json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"{out} · {len(ITEMS)}칸")


if __name__ == "__main__":
    main(*sys.argv[1:])
