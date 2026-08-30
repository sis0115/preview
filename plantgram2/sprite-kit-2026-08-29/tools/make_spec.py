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
HEAD = 64
COLS, ROWS = 4, 2
CW, CH = W // COLS, (H - HEAD) // ROWS      # 384 x 480

TW, TH = 160, 80                            # 표준 타일. 정확히 2 : 1
GX, GY = CW // 2, 390                       # 칸 안에서 바닥 한가운데

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
ITEMS = [
    dict(id="pot_round", kind="화분", name="둥근 화분",
         foot=[(0, 0)], soil=55, slots=[("1x1", (0, 0))],
         note="테라코타. 밑면이 타일을 꽉 채우게"),
    dict(id="bed_long", kind="화분", name="긴 화단",
         foot=[(0, 0), (0, -1)], soil=58,
         slots=[("1x1", (0, 0)), ("1x1", (0, -1))],
         note="나무. 같은 식물을 두 그루 심는 자리"),
    dict(id="planter_big", kind="화분", name="큰 화분",
         foot=[(0, 0), (1, 0), (0, -1), (1, -1)], soil=72,
         slots=[("2x2", None)],
         note="시멘트. 큰 나무 한 그루"),
    dict(id="shelf", kind="가구", name="선반",
         foot=[(0, 0), (0, -1)],
         shelves=[(62, "아래 판"), (152, "위 판")],
         note="층마다 작은 화분 두 개"),
    dict(id="plant_s", kind="식물", name="작은 식물",
         foot=[(0, 0)], fits="1x1", note="선반에 올릴 작은 것"),
    dict(id="plant_m", kind="식물", name="식물",
         foot=[(0, 0)], fits="1x1", note="몬스테라 같은 관엽"),
    dict(id="plant_tall", kind="식물", name="키 큰 식물",
         foot=[(0, 0)], fits="1x1", note="대나무처럼 위로 자라는 것"),
    dict(id="plant_big", kind="식물", name="큰 식물",
         foot=[(0, 0), (1, 0), (0, -1), (1, -1)], fits="2x2",
         note="야자처럼 큰 나무"),
]


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


def foot_centers(foot):
    """밑면 타일들의 한가운데. 덩어리 전체가 바닥 기준점에 오도록 옮깁니다."""
    u, v = (TW / 2, TH / 2), (-TW / 2, TH / 2)
    pts = [(u[0] * i + v[0] * j, u[1] * i + v[1] * j) for i, j in foot]
    ox = sum(p[0] for p in pts) / len(pts)
    oy = sum(p[1] for p in pts) / len(pts)
    return [(GX + p[0] - ox, GY + p[1] - oy) for p in pts]


def draw_cell(dr, ox, oy, n, it):
    dr.rounded_rectangle([ox + 6, oy + 6, ox + CW - 6, oy + CH - 6], 14,
                         fill=CARD, outline=EDGE)

    dr.text((ox + 18, oy + 16), f"{n}. {it['name']}", font=font(19, True), fill=INK)
    spread = {1: "1칸", 2: "2칸", 4: "4칸(2×2)"}[len(it["foot"])]
    what = "퍼지는 범위" if it["kind"] == "식물" else "밑면"
    tail = " · 키는 자유" if it["kind"] == "식물" else ""
    dr.text((ox + 18, oy + 41), f"{it['kind']} · {what} {spread}{tail}",
            font=font(14), fill=MUTE)
    dr.text((ox + 18, oy + 61), it["note"], font=font(13), fill=MUTE)

    cs = [(ox + x, oy + y) for x, y in foot_centers(it["foot"])]
    gx, gy = ox + GX, oy + GY
    base = hull([p for c in cs for p in diamond(*c)])

    # 밑판 — 여기에 놓입니다
    dr.polygon(base, fill=TILE, outline=TILE_E)
    for c in cs:
        dr.polygon(diamond(*c), outline=TILE_E)
        dr.ellipse([c[0] - 2, c[1] - 2, c[0] + 2, c[1] + 2], fill=TILE_E)

    # 밑면의 좌우 끝을 위로 세워 둡니다. 잎이 넘지 말아야 할 선입니다.
    lx = min(base, key=lambda p: p[0])
    rx = max(base, key=lambda p: p[0])
    for px, py in (lx, rx):
        y = py
        while y > oy + 96:
            dr.line([(px, y), (px, y - 7)], fill=(240, 194, 160), width=1)
            y -= 13

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


def main(out="sheets/spec_01.png"):
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)

    dr.text((24, 14), "규격 시험지 — 안내선 위에 그려 주세요",
            font=font(22, True), fill=INK)
    dr.text((24, 42),
            f"타일 {TW}×{TH} (정확히 2:1)    "
            "초록 마름모 = 밑면이 덮을 자리(좌우로 넘지 않기) · "
            "갈색 면 = 흙 윗면 / 선반 판 · 주황 십자 = 식물이 놓일 점 · "
            "키는 자유        ※ 안내선과 글자는 결과물에 그리지 마세요",
            font=font(14), fill=MUTE)

    spec = {"width": W, "height": H, "tileW": TW, "tileH": TH, "items": []}

    for n, it in enumerate(ITEMS):
        ox = (n % COLS) * CW
        oy = HEAD + (n // COLS) * CH
        draw_cell(dr, ox, oy, n + 1, it)

        cs = [(ox + x, oy + y) for x, y in foot_centers(it["foot"])]
        rec = {"id": it["id"], "kind": it["kind"], "cell": n,
               "box": [ox, oy, ox + CW, oy + CH],
               "ground": [ox + GX, oy + GY],
               "foot": it["foot"],
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
                    rec["slots"].append(
                        {"kind": kind, "x": ox + GX, "y": ox * 0 + oy + GY - it["soil"]})
                else:
                    i = it["foot"].index(cell)
                    rec["slots"].append({"kind": kind, "x": round(cs[i][0]),
                                         "y": round(cs[i][1] - it["soil"])})
        spec["items"].append(rec)

    im.save(out)
    json.dump(spec, open(out.replace(".png", ".json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"{out} · {len(ITEMS)}칸 · 타일 {TW}x{TH} · 키 제한 없음")


if __name__ == "__main__":
    main(*sys.argv[1:])
