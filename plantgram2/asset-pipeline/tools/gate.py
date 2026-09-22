"""돌아온 시트를 들여보낼지 말지 **기계가** 정합니다.

지금까지는 제가 눈으로 보고 "괜찮은 것 같다"고 했습니다. 조각이 수십 개가
되면 그렇게 못 합니다. 합격 기준을 글로 적고, 통과 못 하면 들이지 않습니다.

    python3 tools/gate.py sheets/f2.png shelf_two bench xlarge bed_long
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
import measure                                    # noqa: E402

CATALOG = "../app-kit/assets/catalog.json"
FONT = "../app-kit/assets/fonts/{}.otf"
ANCHOR_W = 301.0          # 기준 조각(긴 화단)이 무대에서 갖는 폭

# 합격 기준. 숫자를 코드에 흩뿌리지 않고 여기 모읍니다.
RULE = {
    "residuePct": 0.30,   # 남은 배경
    "minOpaque": 3000,    # 너무 작으면 잘못 잘린 것
    "anchorTol": 0.06,    # 기준 조각이 이만큼 넘게 다르면 축척을 못 믿습니다
    "gradeStep": 1.08,    # 등급은 적어도 이만큼씩 커져야 구분됩니다
}


def font(s, b=False):
    return ImageFont.truetype(
        FONT.format("Pretendard-SemiBold" if b else "Pretendard-Regular"), s)


def check(sheet, ids, anchor="bed_long"):
    grid = json.load(open(CATALOG, encoding="utf-8"))["grid"]
    got = measure.cut(sheet)
    out = {"sheet": sheet, "wanted": ids, "found": len(got), "pieces": [], "pass": True}

    if len(got) != len(ids):
        out["pass"] = False
        out["error"] = f"조각이 {len(got)}개입니다. {len(ids)}개를 기대했습니다."
        return out, got, 1.0

    if anchor not in ids:
        out["pass"] = False
        out["error"] = f"기준 조각 {anchor} 이 시트에 없습니다. 축척을 맞출 수 없습니다."
        return out, got, 1.0

    ref = got[ids.index(anchor)][1]
    art_to_kit = ANCHOR_W / ref.width
    art_to_stage = art_to_kit * grid["unitScale"]

    for (box, art), pid in zip(got, ids):
        h = measure.alpha_health(art)
        b = measure.base(art, grid, art_to_stage)
        bad = []
        if h["residuePct"] > RULE["residuePct"]:
            bad.append(f"배경 잔재 {h['residuePct']}% > {RULE['residuePct']}%")
        if h["opaque"] < RULE["minOpaque"]:
            bad.append(f"너무 작습니다 ({h['opaque']}px)")
        if pid == anchor:
            # 기준 조각은 지난 시트와 모양까지 같아야 축척을 믿을 수 있습니다.
            for k, want in (("spanU", .64), ("spanV", 2.02)):
                if abs(b[k] - want) / want > RULE["anchorTol"]:
                    bad.append(f"기준 조각 {k} {b[k]:.2f} ≠ {want} "
                               f"({RULE['anchorTol']*100:.0f}% 넘게 다름)")
        out["pieces"].append({
            "id": pid, "w": art.width, "h": art.height,
            "stageW": round(art.width * art_to_stage, 1),
            **h, **b, "pass": not bad, "why": bad})
        if bad:
            out["pass"] = False

    # 등급 사다리 — 화분·식물은 등급마다 눈에 띄게 커져야 합니다.
    order = [p for g in ("sprout", "small", "medium", "large", "xlarge")
             for p in out["pieces"] if p["id"] in (g, "pot_" + g)]
    for a, c in zip(order, order[1:]):
        if c["stageW"] < a["stageW"] * RULE["gradeStep"]:
            c["pass"] = False
            c["why"].append(f"{a['id']}({a['stageW']})보다 "
                            f"{RULE['gradeStep']}배 크지 않습니다 ({c['stageW']})")
            out["pass"] = False
    return out, got, art_to_stage


def report(out, got, png="sheets/gate.png"):
    W, cell = 1560, 300
    rows = (len(got) + 4) // 5
    im = Image.new("RGBA", (W, 150 + rows * (cell + 92)), (244, 243, 239, 255))
    d = ImageDraw.Draw(im)
    ok = out["pass"]
    d.text((40, 30), "합격" if ok else "불합격", font=font(34, True),
           fill=(38, 122, 78) if ok else (196, 62, 48))
    d.text((40, 76), out.get("error", f"조각 {out['found']}개 · "
           f"기준 {', '.join(f'{k} {v}' for k, v in RULE.items())}"),
           font=font(16), fill=(120, 130, 138))

    for n, ((box, art), p) in enumerate(zip(got, out["pieces"])):
        x = 40 + (n % 5) * cell
        y = 150 + (n // 5) * (cell + 92)
        k = min(1.0, (cell - 40) / max(art.width, art.height))
        a = art.resize((max(1, round(art.width * k)), max(1, round(art.height * k))),
                       Image.LANCZOS)
        im.alpha_composite(a, (x, y + cell - 30 - a.height))
        tint = (38, 122, 78) if p["pass"] else (196, 62, 48)
        d.text((x, y + cell), f"{'○' if p['pass'] else '✕'} {p['id']}",
               font=font(17, True), fill=tint)
        d.text((x, y + cell + 24),
               f"{p['w']}×{p['h']} → 무대 {p['stageW']}\n"
               f"칸 {p['cells'][0]}×{p['cells'][1]} · 잔재 {p['residuePct']}%",
               font=font(13), fill=(120, 130, 138))
        if not p["pass"]:
            d.text((x, y + cell + 62), " / ".join(p["why"])[:44],
                   font=font(12), fill=tint)
    im.convert("RGB").save(png)
    return png


if __name__ == "__main__":
    sheet, ids = sys.argv[1], sys.argv[2:]
    out, got, _ = check(sheet, ids)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:1200])
    if got:
        print("\n" + report(out, got))
    print("\n판정:", "합격" if out["pass"] else "불합격 — 들이지 않습니다")
    sys.exit(0 if out["pass"] else 1)
