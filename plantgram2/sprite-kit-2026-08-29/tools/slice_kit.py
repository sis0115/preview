"""받은 예제 한 벌을 잘라 Flutter 앱이 쓸 에셋으로 내보냅니다.

기준점을 찾지 않습니다. 우리가 그려 보낸 자리가 kit_ref.json 에 있으므로
그대로 씁니다. 그림자는 요청하지 않고 여기서 그립니다 - 화분마다 폭을
맞출 수 있고 부드러운 타원이라 코드가 더 정확합니다.

    python3 tools/slice_kit.py sheets/kit.png ../app-kit/assets
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter


def trim(im, pad=4):
    """불투명 영역만 남기고 오립니다. 잘라낸 만큼의 이동량도 돌려줍니다."""
    bb = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    if bb is None:
        return im, 0, 0
    x0 = max(0, bb[0] - pad)
    y0 = max(0, bb[1] - pad)
    x1 = min(im.width, bb[2] + pad)
    y1 = min(im.height, bb[3] + pad)
    return im.crop((x0, y0, x1, y1)), x0, y0


def make_shadow(width, path):
    """접지 그림자. 진한 반투명이라 어떤 바닥에서도 얼룩이 되지 않습니다."""
    w = round(width * 1.25)
    h = round(w / 2.6)
    pad = round(w * .3)
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([pad, pad, pad + w, pad + h],
                               fill=(64, 52, 38, 70))
    im = im.filter(ImageFilter.GaussianBlur(pad * .38))
    im.save(path)
    return {"w": im.width, "h": im.height,
            "anchorX": im.width // 2, "anchorY": im.height // 2}


def main(sheet_path, out="assets", ref="sheets/kit_ref.json"):
    m = json.load(open(ref))
    sheet = Image.open(sheet_path).convert("RGBA")
    if sheet.size != (m["width"], m["height"]):
        sheet = sheet.resize((m["width"], m["height"]), Image.LANCZOS)
        print(f"크기를 {sheet.size} 로 맞췄습니다")

    for d in ("greenhouse", "pots", "plants", "shadows"):
        os.makedirs(f"{out}/{d}", exist_ok=True)

    st = m["stage"]
    stage = sheet.crop((st["x"], st["y"], st["x"] + st["w"], st["y"] + st["h"]))
    stage.convert("RGB").save(f"{out}/greenhouse/stage.png")

    cat = {"pots": {}, "plants": {}, "grid": {
        "iso": m["iso"], "n": st["grid"], "tileW": st["tileW"],
        "tileH": st["tileH"], "originX": st["originX"], "originY": st["originY"],
        "sceneW": st["w"], "sceneH": st["h"]}}

    for p in m["pieces"]:
        x0, y0, x1, y1 = p["box"]
        cell = sheet.crop((x0, y0, x1, y1))
        art, dx, dy = trim(cell)
        if p["kind"] == "pot":
            # 심는 자리를 오려낸 그림 안의 좌표로 옮깁니다
            slots = [{"x": s["x"] - x0 - dx, "y": s["y"] - y0 - dy, "w": s["w"]}
                     for s in p["slots"]]
            art.save(f"{out}/pots/{p['id']}.png")
            cat["pots"][p["id"]] = {
                "w": art.width, "h": art.height, "slots": slots,
                "bottom": art.height,
                "shadow": make_shadow(slots[0]["w"],
                                      f"{out}/shadows/{p['id']}.png"),
            }
        else:
            a = p["anchor"]
            art.save(f"{out}/plants/{p['id']}.png")
            cat["plants"][p["id"]] = {
                "w": art.width, "h": art.height,
                "stemX": a["x"] - x0 - dx, "stemY": a["y"] - y0 - dy,
            }
        print(f"  {p['id']:16} {art.width:4}x{art.height:<4}")

    json.dump(cat, open(f"{out}/catalog.json", "w"), indent=1, ensure_ascii=False)
    print(f"\n무대 {stage.width}x{stage.height} · 화분 {len(cat['pots'])} · "
          f"식물 {len(cat['plants'])} → {out}/catalog.json")


if __name__ == "__main__":
    main(*sys.argv[1:])
