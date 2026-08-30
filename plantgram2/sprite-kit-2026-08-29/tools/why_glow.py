"""새 시트를 왜 못 자르는지 눈으로 보여 줍니다.

배경이 검정이어도 조각마다 빛 번짐(글로우)이 깔려 있으면, 조각 바깥의
번짐 색이 조각 안쪽 색과 똑같아집니다. 그러면 어떤 기준값으로도 경계를
찾을 수 없습니다. 이 그림은 그 사실을 재서 보여 주는 증거입니다.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = "sheets/grade_art2.png"
OUT = "sheets/glow_evidence.png"
FONT = "../app-kit/assets/fonts/{}.otf"
INK, DIM, RED = (34, 40, 44), (120, 130, 138), (196, 62, 48)


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def hexs(c):
    return "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in c)


def main():
    src = Image.open(SRC).convert("RGB")
    a = np.asarray(src).astype(float) / 255

    # 화분 사이 빈 곳(번짐)과 바로 옆 화분 몸통에서 한 점씩.
    gap, body = (380, 430), (300, 430)     # (x, y)
    cg, cb = a[gap[1], gap[0]], a[body[1], body[0]]

    W, H = 1400, 940
    im = Image.new("RGB", (W, H), (247, 246, 243))
    d = ImageDraw.Draw(im)

    d.text((44, 36), "이 시트는 자를 수 없습니다", font=font(38, True), fill=INK)
    d.text((44, 88), "배경은 검정인데 조각마다 빛 번짐이 깔려 있어서, "
                     "조각 바깥과 안쪽 색이 같습니다.", font=font(20), fill=DIM)

    # 왼쪽 — 4배 확대한 경계 부분
    cx, cy, half = 340, 420, 60
    crop = src.crop((cx - half, cy - half, cx + half, cy + half)) \
              .resize((half * 2 * 4, half * 2 * 4), Image.NEAREST)
    im.paste(crop, (44, 150))
    d.rectangle([44, 150, 44 + 480, 150 + 480], outline=(210, 208, 202))
    d.text((44, 646), "화분 왼쪽 경계를 4배로 본 모습", font=font(19, True), fill=INK)
    d.text((44, 676), "선이 어디인지 보이지 않습니다. 번짐이 화분 색 그대로\n"
                      "바깥까지 이어집니다.", font=font(17), fill=DIM)

    # 오른쪽 — 두 점의 색
    x0 = 580
    d.text((x0, 150), "같은 그림에서 찍은 두 점", font=font(24, True), fill=INK)
    rows = [("화분 바깥 · 빈 곳 (번짐)", cg, gap),
            ("화분 안쪽 · 몸통",        cb, body)]
    y = 200
    for label, c, pt in rows:
        d.rectangle([x0, y, x0 + 92, y + 92],
                    fill=tuple(int(v * 255) for v in c), outline=(190, 188, 182))
        d.text((x0 + 112, y + 12), label, font=font(20, True), fill=INK)
        d.text((x0 + 112, y + 42), f"{hexs(c)}   ·  x={pt[0]} y={pt[1]}",
               font=font(18), fill=DIM)
        y += 124

    diff = float(np.abs(cg - cb).max()) * 255
    d.text((x0, y + 8), f"두 색의 차이 : {diff:.0f} / 255",
           font=font(22, True), fill=RED)
    d.text((x0, y + 42),
           "배경과 조각이 같은 색이면 나눌 기준을 세울 수 없습니다.\n"
           "밝기로 잘라도, 색으로 잘라도 화분이 함께 잘려 나갑니다.",
           font=font(18), fill=DIM)

    # 아래 — 잘라 보면 이렇게 됩니다
    d.text((x0, y + 130), "밝기 0.5 로 잘라 본 결과", font=font(20, True), fill=INK)
    m = (a.max(2) > .5)
    prev = Image.fromarray(np.where(m[..., None], 255, 40).astype(np.uint8)
                           .repeat(3, 2)).resize((760, 507))
    im.paste(prev.crop((0, 0, 760, 380)), (x0, y + 164))
    d.rectangle([x0, y + 164, x0 + 760, y + 544], outline=(210, 208, 202))

    d.text((44, 790), "필요한 것", font=font(24, True), fill=INK)
    d.text((44, 830),
           "그림은 그대로 두고 배경만 · 번짐 없이 · 완전히 평평한 한 가지 색으로.\n"
           "검정은 잎 그늘과 섞이니 마젠타(#FF00FF)가 안전합니다.",
           font=font(19), fill=DIM)

    im.save(OUT)
    print(f"{OUT}  ·  두 색 차이 {diff:.0f}/255")


if __name__ == "__main__":
    main()
