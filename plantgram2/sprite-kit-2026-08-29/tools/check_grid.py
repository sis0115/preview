"""돌아온 온실 그림에 우리 격자를 얹어 어긋났는지 확인합니다.

stage_ref.json 의 36칸 좌표에 점을 찍습니다. 점이 타일 한가운데에
떨어지면 그대로 쓰면 되고, 밀려 있으면 몇 픽셀인지 재서 보정하거나
되돌려보냅니다.

    python3 tools/check_grid.py sheets/stage.png
"""
import json, sys
from PIL import Image, ImageDraw

def main(path, ref="sheets/stage_ref.json", out=None):
    meta = json.load(open(ref))
    im = Image.open(path).convert("RGB")
    if (im.width, im.height) != (meta["width"], meta["height"]):
        print(f"크기가 다릅니다 {im.width}x{im.height} — 기준은 "
              f"{meta['width']}x{meta['height']}. 비율로 맞춥니다.")
    kx = im.width / meta["width"]
    ky = im.height / meta["height"]
    dr = ImageDraw.Draw(im)
    hw = meta["tileW"] * kx / 2
    hh = meta["tileH"] * ky / 2
    for c in meta["cells"]:
        x, y = c["x"] * kx, c["y"] * ky
        dr.polygon([(x, y - hh), (x + hw, y), (x, y + hh), (x - hw, y)],
                   outline=(255, 90, 0))
        dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 90, 0))
    out = out or path.replace(".png", "_grid.png")
    im.save(out)
    print(f"{out} — 점 {len(meta['cells'])}개가 타일 한가운데에 있는지 보세요")

if __name__ == "__main__":
    main(*sys.argv[1:])
