"""텃밭(긴 화단)이 두 칸에 어떻게 들어가는지 봅니다.

화단을 줄이면 심는 자리 간격도 같이 줄고, 그러면 거기 심을 소형도 줄여야
합니다. 셋이 묶여 있으므로 따로 정할 수 없습니다.

    python3 tools/make_bed_preview.py sheets/bed_preview.png
"""
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from scene_test import load, shadow          # noqa: E402

TILE, ISO = 225.0, 1.73
BG = (243, 242, 237)
INK = (46, 64, 52)
MUTE = (140, 150, 143)
TILEC = (214, 226, 208)
TILEE = (150, 176, 144)
MARK = (232, 106, 30)
BLUE = (40, 100, 200)
FONT = "../app-kit/assets/fonts/{}.otf"


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def main(out="sheets/bed_preview.png"):
    piece = load()
    bed = piece["bed_long"]
    small = piece["plant_s"]
    hw, hh = TILE / 2, TILE / 2 / ISO
    span = hw * 3                      # 두 칸 덩어리의 가로 폭
    W, H = 1400, 700
    im = Image.new("RGBA", (W, H), BG + (255,))
    dr = ImageDraw.Draw(im)
    dr.text((24, 18), "텃밭이 두 칸에 어떻게 들어가나",
            font=font(22, True), fill=INK)
    dr.text((24, 48),
            "파란 점 = 칸 한가운데 · 주황 점 = 화단의 심는 자리. "
            "둘이 겹쳐야 두 그루가 각자의 칸에 앉습니다.",
            font=font(14), fill=MUTE)

    for n, k in enumerate((1.0, .82)):
        cx, base = 380 + n * 660, 400
        # 두 칸
        for j in (0, 1):
            x = cx + (-hw) * (j - .5)
            y = base + hh * (j - .5)
            dr.polygon([(x, y - hh), (x + hw, y), (x, y + hh), (x - hw, y)],
                       fill=TILEC, outline=TILEE)
            dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=BLUE)

        art = bed["art"]
        w = round(art.width * k)
        a = art.resize((w, round(art.height * k)), Image.LANCZOS)
        fx, fy = bed["foot"][0] * k, bed["foot"][1] * k
        sh = shadow(a.width * .8, ISO)
        im.alpha_composite(sh, (round(cx - sh.width / 2), round(base - sh.height / 2)))
        a.putalpha(a.getchannel("A").point(lambda v: round(v * .88)))
        im.alpha_composite(a, (round(cx - fx), round(base - fy)))

        # 심는 자리와 거기 심을 소형
        spots = [(x * k, y * k) for x, y in bed["anchor"]]
        gap = abs(spots[1][0] - spots[0][0])
        plant_w = min(gap - 8, 101 * k / 1)          # 안 겹치는 최대 폭
        s = plant_w / small["art"].width
        leaf = small["art"].resize((round(small["art"].width * s),
                                    round(small["art"].height * s)), Image.LANCZOS)
        sx, sy = small["anchor"][0][0] * s, small["anchor"][0][1] * s
        for ax, ay in sorted(spots, key=lambda p: p[1]):
            im.alpha_composite(leaf, (round(cx - fx + ax - sx),
                                      round(base - fy + ay - sy)))
            dr.ellipse([cx - fx + ax - 5, base - fy + ay - 5,
                        cx - fx + ax + 5, base - fy + ay + 5], fill=MARK)

        # 두 칸 폭 치수선
        y0 = base + 120
        dr.line([(cx - span / 2, y0), (cx + span / 2, y0)], fill=TILEE, width=2)
        dr.text((cx, y0 - 8), f"두 칸 {round(span)}px", font=font(13),
                fill=(90, 120, 88), anchor="ms")
        y1 = y0 + 34
        dr.line([(cx - w / 2, y1), (cx + w / 2, y1)], fill=MARK, width=2)
        dr.text((cx, y1 - 8), f"화단 {w}px  (두 칸의 {w / span:.0%})",
                font=font(13, True), fill=MARK, anchor="ms")

        dr.text((cx, base + 190),
                "지금 크기" if k == 1 else f"{k:.0%} 로 줄이면",
                font=font(19, True), fill=INK, anchor="ms")
        dr.text((cx, base + 216),
                f"심는 자리 간격 {gap:.0f}px  (칸 간격 {hw:.0f}px)",
                font=font(13), fill=MUTE, anchor="ms")
        dr.text((cx, base + 238),
                f"거기 심을 소형은 {round(plant_w)}px 이하",
                font=font(13, True), fill=(60, 130, 80) if k == 1 else (198, 90, 50),
                anchor="ms")
        print(f"{'지금' if k==1 else '줄이면'}: 화단 {w}px ({w/span:.0%}) · "
              f"자리 간격 {gap:.0f}px · 소형 ≤ {round(plant_w)}px")

    im.convert("RGB").save(out)
    print(f"\n{out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
