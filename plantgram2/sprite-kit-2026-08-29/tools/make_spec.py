"""규격 시험지를 그립니다. 우리가 기하를 정하고, 그림은 그 안에 들어옵니다.

지금까지는 그림을 받고 나서 기하를 알아내려 했습니다 - 흙을 색으로 찾고,
줄기를 실루엣으로 찾고, 바닥 꼭짓점에서 격자를 되짚었습니다. 매번 틀렸고,
시트가 바뀌면 또 틀립니다.

여기서는 뒤집습니다. 칸마다 밑면이 덮을 타일과 흙이 놓일 높이를 우리가 먼저
그려 보냅니다.

키는 정하지 않습니다. 밑면만 맞으면 놓는 데 아무 문제가 없고, 키까지 묶으면
그림 쪽 자율성만 깎입니다 - 키가 크든 작든 같은 자리에 놓입니다. 돌아온 그림은 **재지 않습니다** - 그 자리에 그렸는지
확인만 하고(verify_spec.py), 좌표는 우리가 보낸 spec.json 을 그대로 씁니다.

    python3 tools/make_spec.py sheets/spec_01.png
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1536, 1024
HEAD = 84
ROWS = 2
CH = (H - HEAD) // ROWS                     # 478
GY = 384                                    # 칸 안에서 바닥 한가운데

TW, TH = 160, 80                            # 표준 타일. 정확히 2 : 1

# 칸 너비는 밑면보다 조금만 큽니다.
#
# 첫 시험지는 칸이 384px 인데 마름모가 160px 이었습니다. 칸의 42% 밖에 안 되는
# 빈 상자를 주니 "보기 좋게 채운" 크기로 그려 왔고, 전부 1.09~2.26배 커졌습니다.
# 채울 여백을 없앱니다.
PAD = 34                                    # 한계선 좌우로 남기는 여백

BG = (242, 241, 236)
CARD = (252, 252, 250)
EDGE = (219, 219, 212)
INK = (46, 64, 52)
MUTE = (140, 150, 143)
TILE = (222, 234, 218)
TILE_E = (126, 160, 122)
MARK = (232, 106, 30)
SOIL = (140, 96, 56)

FONT = "../app-kit/assets/fonts/{}.otf"

# 슬롯 등급: 식물 한 그루가 들어가는 자리의 크기입니다.
#   "1x1" 한 칸짜리 · "2x1" 두 칸짜리 · "2x2" 네 칸짜리
# width 는 이 물건이 실제로 얼마나 넓은지입니다. 칸(밑면)은 그 결과일 뿐,
# 채워야 할 목표가 아닙니다 - 작은 것을 늘려서 칸을 채우면 다른 물건이 아니라
# 뭉개진 같은 물건이 됩니다.
#
# hint 는 크기 보기입니다. 자연스러운 배율(0.5~1.15배)로 보여 줄 수 있는
# 그림이 있을 때만 씁니다. 특대형은 늘린 그림 대신 치수선으로만 알려 줍니다.
ITEMS = [
    dict(id="pot_round", kind="화분", name="둥근 화분",
         foot=[(0, 0)], width=160, soil=55, slots=[("1x1", (0, 0))],
         hint="pots/pot_terracotta",
         note="테라코타. 흔한 크기"),
    dict(id="bed_long", kind="화분", name="긴 화단",
         foot=[(0, 0), (0, -1)], width=240, soil=58,
         slots=[("1x1", (0, 0)), ("1x1", (0, -1))],
         hint="pots/bed_wood",
         note="나무. 길어서 두 칸. 같은 식물을 두 그루"),
    dict(id="planter_big", kind="화분", name="큰 화분",
         foot=[(0, 0), (1, 0), (0, -1), (1, -1)], width=320, soil=72,
         slots=[("2x2", None)], hint=None,
         note="특대형 석재 화분. 원래 커서 네 칸"),
    dict(id="shelf", kind="가구", name="선반",
         foot=[(0, 0), (0, -1)], width=240,
         shelves=[(62, "아래 판"), (152, "위 판")], hint="box",
         note="층마다 작은 화분 두 개"),
    dict(id="plant_s", kind="식물", name="작은 식물",
         foot=[(0, 0)], width=120, fits="1x1", hint="plants/strelitzia",
         note="선반에 올라갈 만큼 작은 것"),
    dict(id="plant_m", kind="식물", name="식물",
         foot=[(0, 0)], width=240, fits="1x1", hint="plants/monstera",
         note="몬스테라 같은 관엽. 흔한 크기"),
    dict(id="plant_tall", kind="식물", name="키 큰 식물",
         foot=[(0, 0)], width=200, fits="1x1", hint="plants/bamboo",
         note="대나무처럼 좁고 위로 자라는 것"),
    dict(id="plant_big", kind="식물", name="특대형 식물",
         foot=[(0, 0), (1, 0), (0, -1), (1, -1)], width=400, fits="2x2",
         hint=None, note="야자처럼 원래 큰 나무. 잎이 넓어 네 칸"),
]


def foot_width(foot):
    """밑면 마름모 덩어리의 가로 너비."""
    return round(TW * {1: 1.0, 2: 1.5, 4: 2.0}[len(foot)])


def allowed(it):
    """이 물건의 실제 가로 너비. 칸을 채우라는 뜻이 아닙니다."""
    return it["width"]


def cell_width(it):
    """칸은 허용 너비보다 조금만 큽니다. 채울 여백을 남기지 않습니다."""
    return allowed(it) + PAD * 2


def font(size, bold=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if bold else "Pretendard-Regular"), size)


def diamond(cx, cy, hw=TW / 2, hh=TH / 2):
    return [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]


def hull(pts):
    """밑면 타일들을 감싸는 바깥 테두리. 상자를 세울 밑판입니다."""
    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and turn(out[-2], out[-1], p) <= 0:
                out.pop()
            out.append(p)
        return out

    return half(pts)[:-1] + half(pts[::-1])[:-1]


def up(poly, dy):
    return [(x, y - dy) for x, y in poly]


def outline(dr, poly, color, width=2, dash=False):
    n = len(poly)
    for k in range(n):
        a, b = poly[k], poly[(k + 1) % n]
        if not dash:
            dr.line([a, b], fill=color, width=width)
            continue
        steps = max(2, int(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** .5 / 11))
        for t in range(steps):
            if t % 2:
                continue
            p = (a[0] + (b[0] - a[0]) * t / steps, a[1] + (b[1] - a[1]) * t / steps)
            q = (a[0] + (b[0] - a[0]) * (t + 1) / steps,
                 a[1] + (b[1] - a[1]) * (t + 1) / steps)
            dr.line([p, q], fill=color, width=width)


def cross(dr, x, y, r=9, color=MARK, width=3):
    dr.line([(x - r, y), (x + r, y)], fill=color, width=width)
    dr.line([(x, y - r), (x, y + r)], fill=color, width=width)


def foot_centers(foot, cw):
    """밑면 타일들의 한가운데. 덩어리 전체가 바닥 기준점에 오도록 옮깁니다."""
    u, v = (TW / 2, TH / 2), (-TW / 2, TH / 2)
    pts = [(u[0] * i + v[0] * j, u[1] * i + v[1] * j) for i, j in foot]
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    return [(cw / 2 + p[0] - mx, GY + p[1] - my) for p in pts]


def draw_cell(dr, im, ox, oy, cw, n, it):
    dr.rounded_rectangle([ox + 6, oy + 6, ox + cw - 6, oy + CH - 6], 14,
                         fill=CARD, outline=EDGE)

    dr.text((ox + 18, oy + 16), f"{n}. {it['name']}", font=font(19, True), fill=INK)
    spread = {1: "1칸", 2: "2칸", 4: "4칸(2×2)"}[len(it["foot"])]
    # 폭은 치수선이 말해 줍니다. 좁은 칸에서는 글자가 넘칩니다.
    line = f"{it['kind']} · 차지하는 자리 {spread}"
    dr.text((ox + 18, oy + 40), line, font=font(13), fill=MUTE)
    dr.text((ox + 18, oy + 58), it["note"], font=font(12), fill=MUTE)

    cs = [(ox + x, oy + y) for x, y in foot_centers(it["foot"], cw)]
    gx, gy = ox + cw / 2, oy + GY
    base = hull([p for c in cs for p in diamond(*c)])

    # 밑판 — 여기에 놓입니다
    dr.polygon(base, fill=TILE, outline=TILE_E)
    for c in cs:
        dr.polygon(diamond(*c), outline=TILE_E)
        dr.ellipse([c[0] - 2, c[1] - 2, c[0] + 2, c[1] + 2], fill=TILE_E)

    # 좌우 한계선. 이 밖으로 나가면 안 됩니다.
    half = allowed(it) / 2
    for px in (gx - half, gx + half):
        y = gy + TH / 2
        while y > oy + 112:
            dr.line([(px, y), (px, y - 7)], fill=(238, 176, 132), width=2)
            y -= 13
    # 치수선. 채우라는 뜻이 아니라 이 물건이 이만큼 넓다는 뜻입니다.
    y = oy + 106
    dr.line([(gx - half, y), (gx + half, y)], fill=MARK, width=2)
    for px, d in ((gx - half, 1), (gx + half, -1)):
        dr.line([(px, y), (px + 7 * d, y - 4)], fill=MARK, width=2)
        dr.line([(px, y), (px + 7 * d, y + 4)], fill=MARK, width=2)
    dr.rectangle([gx - 46, y - 10, gx + 46, y + 10], fill=CARD)
    dr.text((gx, y + 6), f"폭 {allowed(it)}px", font=font(13, True),
            fill=MARK, anchor="ms")

    if it["kind"] == "식물":
        cross(dr, gx, gy)
        dr.text((gx + 13, gy + 7), "줄기 밑동", font=font(13, True), fill=MARK)
        return

    levels = it.get("shelves") or [(it["soil"], "흙 윗면")]
    for h, tag in levels:
        plane = up(base, h)
        outline(dr, plane, SOIL, 2)
        t = min(plane, key=lambda p: p[1])
        dr.text((t[0], t[1] - 17), tag, font=font(13, True), fill=SOIL, anchor="ms")
        if "shelves" in it:
            for c in cs:
                cross(dr, c[0], c[1] - h, r=7, width=2)
        else:
            for kind, cell in it["slots"]:
                if cell is None:
                    cross(dr, gx, gy - h, r=8)
                else:
                    c = cs[it["foot"].index(cell)]
                    cross(dr, c[0], c[1] - h, r=8)


def hint(im, dr, cw, ox, oy, it):
    """크기 보기.

    말로 "점선 안에"라고만 하면 모양 해석이 갈리는 칸에서 어긋납니다.
    2차에서 보기가 있던 칸은 0.99 로 맞았고, 없던 칸 둘이 1.30 · 1.33 이었습니다.

    다만 작은 그림을 늘려서 보여 주면 "늘려서 채우라"는 잘못된 지시가 됩니다.
    자연스러운 배율로 보여 줄 그림이 있을 때만 깔고, 특대형은 치수선으로만
    알려 줍니다.
    """
    cs = foot_centers(it["foot"], cw)
    bottom = (max(y for _, y in cs) + TH / 2) if it["kind"] != "식물" else GY

    if it["hint"] == "box":
        base = hull([p for c in cs for p in diamond(*c)])
        top = up(base, TW)
        g = (182, 182, 176)
        for a, b in zip(base, top):
            dr.line([(ox + a[0], oy + a[1]), (ox + b[0], oy + b[1])], fill=g, width=2)
        outline(dr, [(ox + x, oy + y) for x, y in top], g, 2)
        return
    if it["hint"] is None:
        return

    try:
        art = Image.open(f"../app-kit/assets/{it['hint']}.png").convert("RGBA")
    except FileNotFoundError:
        return
    art = art.resize((allowed(it), round(art.height * allowed(it) / art.width)),
                     Image.LANCZOS)
    art.putalpha(art.getchannel("A").point(lambda v: round(v * .20)))

    # 칸 밖으로 넘치면 옆 칸까지 흐려집니다. 카드 안으로 잘라 붙입니다.
    px = round(ox + cw / 2 - art.width / 2)
    py = round(oy + bottom - art.height)
    card = (ox + 8, oy + 8, ox + cw - 8, oy + CH - 8)
    cut = (max(0, card[0] - px), max(0, card[1] - py),
           min(art.width, card[2] - px), min(art.height, card[3] - py))
    if cut[0] >= cut[2] or cut[1] >= cut[3]:
        return
    art = art.crop(cut)
    im.paste(art, (px + cut[0], py + cut[1]), art)


def main(out="sheets/spec_02.png"):
    im = Image.new("RGBA", (W, H), BG + (255,))
    dr = ImageDraw.Draw(im)

    dr.text((24, 12), "규격 시험지 3 — 칸이 아니라 물건의 크기",
            font=font(21, True), fill=INK)
    dr.text((24, 40),
            f"타일 {TW}×{TH} (정확히 2:1)    "
            "초록 마름모 = 이 물건이 차지하는 자리 · 주황 치수선 = 실제 폭 · "
            "갈색 면 = 흙 윗면 / 선반 판 · 주황 십자 = 식물이 놓일 점 · 키는 자유",
            font=font(13), fill=MUTE)

    dr.text((24, 58),
            "칸이 넓은 것은 물건이 원래 커서입니다. 자리를 채우려고 늘리지 마세요 — "
            "그 크기의 물건을 그려 주세요.        "
            "※ 안내선·글자·흐린 그림은 결과물에 그리지 마세요",
            font=font(13), fill=(198, 118, 70))

    spec = {"width": W, "height": H, "tileW": TW, "tileH": TH, "items": []}

    rows = [ITEMS[:4], ITEMS[4:]]
    for r, row in enumerate(rows):
        widths = [cell_width(it) for it in row]
        ox = (W - sum(widths)) / 2
        oy = HEAD + r * CH
        for it, cw in zip(row, widths):
            n = ITEMS.index(it)
            draw_cell(dr, im, round(ox), oy, cw, n + 1, it)
            hint(im, dr, cw, round(ox), oy, it)

            cs = [(ox + x, oy + y) for x, y in foot_centers(it["foot"], cw)]
            rec = {"id": it["id"], "kind": it["kind"], "cell": n,
                   "box": [round(ox), oy, round(ox + cw), oy + CH],
                   "ground": [round(ox + cw / 2), oy + GY],
                   "foot": it["foot"], "allowW": allowed(it),
                   "tiles": [[round(x), round(y)] for x, y in cs]}
            if it["kind"] == "식물":
                rec["fits"] = it["fits"]
            elif "shelves" in it:
                rec["slots"] = [
                    {"kind": "1x1", "x": round(cx), "y": round(cy - h)}
                    for h, _ in it["shelves"] for cx, cy in cs]
            else:
                rec["soil"] = it["soil"]
                rec["slots"] = []
                for kind, cell in it["slots"]:
                    if cell is None:
                        rec["slots"].append({"kind": kind, "x": round(ox + cw / 2),
                                             "y": oy + GY - it["soil"]})
                    else:
                        i = it["foot"].index(cell)
                        rec["slots"].append({"kind": kind, "x": round(cs[i][0]),
                                             "y": round(cs[i][1] - it["soil"])})
            spec["items"].append(rec)
            ox += cw

    im.convert("RGB").save(out)
    json.dump(spec, open(out.replace(".png", ".json"), "w"),
              indent=1, ensure_ascii=False)
    for it in ITEMS:
        print(f"  {it['id']:12} 허용 너비 {allowed(it):3}px · 칸 {cell_width(it):3}px")
    print(f"{out} · {len(ITEMS)}칸 · 타일 {TW}x{TH}")


if __name__ == "__main__":
    main(*sys.argv[1:])
