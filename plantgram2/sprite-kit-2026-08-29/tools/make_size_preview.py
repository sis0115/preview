"""크기 등급을 눈으로 보는 그림. 요청하기 전에 검토받는 용도입니다.

앞선 시험지는 다섯 칸에 같은 화분을 깔아서 등급끼리 크기 차이가 보이지
않았습니다. 여기서는 다섯 등급을 한 줄에 놓고, 각자 알맞은 화분에 심어
나란히 보여 줍니다.

기준은 **타일 한 칸**입니다. 무대 타일 156.8px 이 조각 시트에서는
156.8 / 0.6969 = 225px 이므로, 등급을 타일 대비로 적으면 그대로 시트 폭이
됩니다.

    python3 tools/make_size_preview.py sheets/size_preview.png
"""
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from scene_test import load, shadow      # noqa: E402

TILE = 225.0        # 조각 시트에서의 타일 폭 (무대 156.8 ÷ 배율 0.6969)
ISO = 1.73

BG = (243, 242, 237)
INK = (46, 64, 52)
MUTE = (140, 150, 143)
TILEC = (216, 226, 210)
TILEE = (168, 188, 162)
MARK = (232, 106, 30)

FONT = "../app-kit/assets/fonts/{}.otf"

# (이름, 타일 대비 폭, 화분, 화분 배율, 밑그림으로 쓸 식물, 차지하는 칸)
GRADES = [
    ("새싹",   .22, "pot_round",   .55, "plant_s",   1),
    ("소형",   .45, "pot_round",   .55, "plant_s",   1),
    ("중형",   .63, "pot_round",   1.0, "plant_s",   1),
    ("대형",   .85, "pot_round",   1.0, "plant_m",   1),
    ("특대형", 1.30, "planter_big", 1.0, "plant_big", 4),
]


def tiles(dr, cx, base, cells):
    """차지하는 칸. 덩어리의 한가운데가 (cx, base) 에 오게 놓습니다."""
    hw, hh = TILE / 2, TILE / 2 / ISO
    u, v = (hw, hh), (-hw, hh)
    origins = [(0, 0)] if cells == 1 else [(0, 0), (1, 0), (0, 1), (1, 1)]
    mi = sum(o[0] for o in origins) / len(origins)
    mj = sum(o[1] for o in origins) / len(origins)
    for i, j in origins:
        x = cx + u[0] * (i - mi) + v[0] * (j - mj)
        y = base + u[1] * (i - mi) + v[1] * (j - mj)
        dr.polygon([(x, y - hh), (x + hw, y), (x, y + hh), (x - hw, y)],
                   fill=TILEC, outline=TILEE)


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def main(out="sheets/size_preview.png"):
    piece = load()
    W, H = 1536, 1180
    base = 660
    im = Image.new("RGBA", (W, H), BG + (255,))
    dr = ImageDraw.Draw(im)

    dr.text((24, 18), "크기 등급 — 이대로 요청할까요?",
            font=font(23, True), fill=INK)
    dr.text((24, 50),
            f"기준은 타일 한 칸. 회색 마름모가 한 칸({round(TILE)}px)입니다. "
            "화분은 그 등급이 심길 자리를 보여 주려고 같이 그렸습니다.        "
            "텃밭(긴 화단)은 지금 크기 그대로 씁니다.",
            font=font(14), fill=MUTE)

    slots = [g[1] * TILE for g in GRADES]
    gap = (W - sum(slots) - 80) / (len(GRADES) + 1)
    x = gap + 40

    print(f"{'등급':6} {'타일 대비':>8} {'시트 폭':>7} {'무대 폭':>7}  화분")
    for (name, k, pot_id, pot_k, plant_id, cells), wid in zip(GRADES, slots):
        cx = x + wid / 2
        tiles(dr, cx, base, cells)

        pot = piece[pot_id]
        pa = pot["art"]
        pw = round(pa.width * pot_k)
        art = pa.resize((pw, round(pa.height * pot_k)), Image.LANCZOS)
        fx, fy = pot["foot"][0] * pot_k, pot["foot"][1] * pot_k
        sh = shadow(art.width * .8, ISO)
        im.alpha_composite(sh, (round(cx - sh.width / 2), round(base - sh.height / 2)))
        im.alpha_composite(art, (round(cx - fx), round(base - fy)))

        pl = piece[plant_id]
        s = wid / pl["art"].width
        leaf = pl["art"].resize((round(pl["art"].width * s),
                                 round(pl["art"].height * s)), Image.LANCZOS)
        sx, sy = pl["anchor"][0][0] * s, pl["anchor"][0][1] * s
        ax, ay = pot["anchor"][0][0] * pot_k, pot["anchor"][0][1] * pot_k
        im.alpha_composite(leaf, (round(cx - fx + ax - sx),
                                  round(base - fy + ay - sy)))

        dr.line([(cx - wid / 2, base + 88), (cx + wid / 2, base + 88)],
                fill=MARK, width=2)
        for px, d in ((cx - wid / 2, 1), (cx + wid / 2, -1)):
            dr.line([(px, base + 88), (px + 7 * d, base + 84)], fill=MARK, width=2)
            dr.line([(px, base + 88), (px + 7 * d, base + 92)], fill=MARK, width=2)
        dr.text((cx, base + 122), name, font=font(19, True), fill=INK, anchor="ms")
        dr.text((cx, base + 146),
                f"한 칸의 {k:.2f}배 · {'한' if cells == 1 else '네'} 칸 차지",
                font=font(13), fill=MUTE, anchor="ms")
        dr.text((cx, base + 166), f"{round(wid)}px", font=font(13, True),
                fill=MARK, anchor="ms")
        print(f"{name:6} {k:8.2f}배 {round(wid):7} {round(wid * .6969):7}  "
              f"{pot_id}{' ×' + str(pot_k) if pot_k != 1 else ''} · "
              f"{cells}칸")
        x += wid + gap

    # 확인 — 긴 화단에 소형 두 그루가 안 겹치는지
    dr.line([(40, 830), (W - 40, 830)], fill=(224, 222, 214), width=1)
    dr.text((40, 856), "확인 — 긴 화단에 소형 두 그루",
            font=font(19, True), fill=INK)
    dr.text((40, 884),
            "심는 자리 간격이 108px 이므로 한 그루가 100px 를 넘으면 겹칩니다. "
            f"소형은 {round(GRADES[1][1] * TILE)}px 입니다.",
            font=font(13), fill=MUTE)

    bed = piece["bed_long"]
    cx, cbase = 420, 1100
    def bed_tiles(cx0):
        hw, hh = TILE / 2, TILE / 2 / ISO
        for j in (0, 1):
            x = cx0 + (-hw) * (j - .5)
            y = cbase + hh * (j - .5)
            dr.polygon([(x, y - hh), (x + hw, y), (x, y + hh), (x - hw, y)],
                       fill=TILEC, outline=TILEE)

    bed_tiles(cx)
    fx, fy = bed["foot"]
    sh = shadow(bed["art"].width * .8, ISO)
    im.alpha_composite(sh, (round(cx - sh.width / 2), round(cbase - sh.height / 2)))
    im.alpha_composite(bed["art"], (round(cx - fx), round(cbase - fy)))
    small = piece["plant_s"]
    sc = GRADES[1][1] * TILE / small["art"].width
    leaf = small["art"].resize((round(small["art"].width * sc),
                                round(small["art"].height * sc)), Image.LANCZOS)
    sx, sy = small["anchor"][0][0] * sc, small["anchor"][0][1] * sc
    for ax, ay in sorted(bed["anchor"], key=lambda p: p[1]):
        im.alpha_composite(leaf, (round(cx - fx + ax - sx),
                                  round(cbase - fy + ay - sy)))

    # 견주기 — 지금 가진 "작은 식물"을 그대로 두 그루 심으면
    cx2 = 1020
    bed_tiles(cx2)
    im.alpha_composite(sh, (round(cx2 - sh.width / 2), round(cbase - sh.height / 2)))
    im.alpha_composite(bed["art"], (round(cx2 - fx), round(cbase - fy)))
    sx0, sy0 = small["anchor"][0]
    for ax, ay in sorted(bed["anchor"], key=lambda p: p[1]):
        im.alpha_composite(small["art"], (round(cx2 - fx + ax - sx0),
                                          round(cbase - fy + ay - sy0)))
    dr.text((cx, cbase + 44), f"소형 {round(GRADES[1][1] * TILE)}px — 안 겹칩니다",
            font=font(14, True), fill=(60, 130, 80), anchor="ms")
    dr.text((cx2, cbase + 44), f"지금 가진 것 {small['art'].width}px — 겹칩니다",
            font=font(14, True), fill=(198, 80, 50), anchor="ms")

    im.convert("RGB").save(out)
    print(f"\n{out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
