"""등급 시트를 실제로 조합해 보고, 온실에도 놓아 봅니다.

    python3 tools/grade_test.py
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from grade_kit import load, scaled           # noqa: E402
from scene_test import shadow                # noqa: E402
from compose_test import soils, cut          # noqa: E402

FONT = "../app-kit/assets/fonts/{}.otf"
SHEET_TILE = 225.0          # 등급을 정한 좌표계에서의 타일 폭

PAIRS = [
    ("새싹", "pot_sprout", "sprout"),
    ("소형", "pot_small", "small"),
    ("중형", "pot_medium", "medium"),
    ("대형", "pot_large", "large"),
    ("특대형", "pot_xlarge", "xlarge"),
    ("긴 화단 + 소형 두 그루", "bed_long", "small"),
]


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def build(pot, plant, iso=1.73):
    """화분에 식물을 심습니다. 심는 자리마다 한 그루씩."""
    sx, sy = plant["anchor"][0]
    boxes = [(0, 0, pot["art"].width, pot["art"].height)]
    for ax, ay in pot["anchor"]:
        boxes.append((ax - sx, ay - sy,
                      ax - sx + plant["art"].width, ay - sy + plant["art"].height))
    l = min(b[0] for b in boxes)
    t = min(b[1] for b in boxes)
    r = max(b[2] for b in boxes)
    b = max(b[3] for b in boxes)
    im = Image.new("RGBA", (round(r - l), round(b - t)), (0, 0, 0, 0))
    im.alpha_composite(pot["art"], (round(-l), round(-t)))
    for ax, ay in sorted(pot["anchor"], key=lambda p: p[1]):
        im.alpha_composite(plant["art"], (round(ax - sx - l), round(ay - sy - t)))
    return im, [(ax - l, ay - t) for ax, ay in pot["anchor"]]


def main(out="sheets/grade_compose.png"):
    piece, unit = load()
    print(f"긴 화단으로 잰 배율 {unit:.4f} — 이전 시트 좌표계로 맞춥니다\n")
    print(f"{'등급':22} {'화분':>6} {'식물':>6} {'식물÷화분':>9}")
    made = []
    for label, pid, plid in PAIRS:
        pot = scaled(piece[pid], unit)
        plant = scaled(piece[plid], unit)
        im, marks = build(pot, plant)
        made.append((label, im, marks))
        print(f"{label:22} {pot['art'].width:6} {plant['art'].width:6} "
              f"{plant['art'].width / pot['art'].width:9.2f}")

    pad = 26
    cw = max(i.width for _, i, _ in made) + pad
    ch = max(i.height for _, i, _ in made) + 70
    zw = cw - pad
    zh = round(zw * 120 / 200)
    sheet = Image.new("RGB", (cw * len(made), ch + zh + 74), (246, 246, 242))
    dr = ImageDraw.Draw(sheet)
    dr.text((16, 14), "등급별 조합 — 아래는 줄기와 흙이 만나는 곳을 4배로",
            font=font(20, True), fill=(46, 64, 52))
    for n, (label, im, marks) in enumerate(made):
        ox = n * cw
        dr.text((ox + cw / 2, 58), label, font=font(13, True),
                fill=(70, 90, 76), anchor="ms")
        px = round(ox + (cw - im.width) / 2)
        py = round(70 + (ch - 70 - im.height))
        sheet.paste(im, (px, py), im)
        mx, my = marks[0]
        crop = im.crop((round(mx - 100), round(my - 70),
                        round(mx + 100), round(my + 50)))
        flat = Image.new("RGB", crop.size, (255, 255, 255))
        flat.paste(crop, (0, 0), crop)
        sheet.paste(flat.resize((zw, zh), Image.LANCZOS), (ox + pad // 2, ch + 36))
        k = zw / 200
        cx, cy = ox + pad // 2 + 100 * k, ch + 36 + 70 * k
        dr.line([(cx - 10, cy), (cx + 10, cy)], fill=(230, 90, 30), width=2)
        dr.line([(cx, cy - 10), (cx, cy + 10)], fill=(230, 90, 30), width=2)
    sheet.save(out)
    print(f"\n{out}")


def scene(out="sheets/grade_scene.png"):
    """온실 배경에 등급별로 놓아 봅니다."""
    from scene_test import load as load4
    grid = json.load(open("sheets/stage_grid.json"))
    T = np.array([grid["topX"], grid["topY"]])
    u = np.array([grid["uX"], grid["uY"]])
    v = np.array([grid["vX"], grid["vY"]])
    iso = grid["tileW"] / grid["tileH"]

    piece, unit = load()
    old = load4()                       # 선반은 이전 시트에서
    to_stage = grid["tileW"] / SHEET_TILE
    print(f"\n무대 배율 {to_stage:.4f} · 등급 시트는 {unit * to_stage:.4f}")

    plan = [
        (0, 2, "pot_xlarge", "xlarge"),
        (2, 0, None, None),                 # 선반
        (1, 4, "pot_large", "large"),
        (4, 2, "bed_long", "small"),
        (3, 4, "pot_medium", "medium"),
        (4, 0, "pot_small", "small"),
        (2, 2, "pot_sprout", "sprout"),
    ]
    centre = lambda i, j: T + u * (i + .5) + v * (j + .5)
    plan.sort(key=lambda p: centre(p[0], p[1])[1])

    stage = Image.open("sheets/stage.png").convert("RGBA")
    for i, j, pid, plid in plan:
        at = centre(i, j)
        if pid is None:
            pot = scaled(old["shelf"], to_stage)
            plant = None
        else:
            pot = scaled(piece[pid], unit * to_stage)
            plant = scaled(piece[plid], unit * to_stage)
        fx, fy = pot["foot"]
        # 다리 달린 것은 마름모 자국. 타원을 깔면 다리 사이가 비어 떠 보입니다.
        # 다리 달린 것은 마름모 자국. 밑면 한가운데는 제 몸에 가려 안 보이므로
        # 자국을 밑면보다 조금 크게 잡아 다리 밖으로 비치게 합니다.
        boxy = pid is None or pid == "bed_long"
        sh = (shadow(pot["art"].width * 1.06, iso, "diamond", ink=150, blur=.22)
              if boxy else shadow(pot["art"].width * .8, iso))
        # 다리 달린 것은 밑면 한가운데가 제 몸에 가립니다. 자국을 다리 끝
        # 쪽으로 조금 내려 앞으로 비치게 합니다.
        drop = (pot["art"].height - fy) * .45 if boxy else 0
        stage.alpha_composite(sh, (round(at[0] - sh.width / 2),
                                   round(at[1] + drop - sh.height / 2)))
        stage.alpha_composite(pot["art"], (round(at[0] - fx), round(at[1] - fy)))
        if plant is None:
            continue
        sx, sy = plant["anchor"][0]
        for ax, ay in sorted(pot["anchor"], key=lambda p: p[1]):
            stage.alpha_composite(plant["art"],
                                  (round(at[0] - fx + ax - sx),
                                   round(at[1] - fy + ay - sy)))
    stage.convert("RGB").save(out)
    print(out)


if __name__ == "__main__":
    main()
    scene()
