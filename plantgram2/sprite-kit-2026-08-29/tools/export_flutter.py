"""Flutter 앱에 넣을 에셋과 정렬점을 내보냅니다.

화분과 식물을 합쳐 굽지 않습니다. 낱장으로 내보내고 정렬점만 적어 두면
앱이 실시간으로 겹칩니다 - 36장으로 288조합이 나오는 이유입니다.

타일은 세로 눌림을 미리 적용해 내보냅니다. 앱에서 매번 늘렸다 줄이면
가장자리가 뭉개집니다.
"""
import json, os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from compose import soil_anchor, stem_anchor
from scene import fit_tile, top_face, ISO

OUT = sys.argv[1] if len(sys.argv) > 1 else "../app-garden/assets/sprites"
Q = 90


def save(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "WEBP", quality=Q, method=6)
    return os.path.getsize(path)


def main():
    meta = {"pots": {}, "plants": {}, "tiles": {}, "iso": ISO}
    total = 0

    for d, kind in [("sliced/pots_round", "pots"), ("sliced/pots_beds", "pots")]:
        for f in sorted(x for x in os.listdir(d) if x.endswith(".png")):
            im = Image.open(f"{d}/{f}").convert("RGBA")
            ax, ay = soil_anchor(im)
            total += save(im, f"{OUT}/pots/{f[:-4]}.webp")
            meta["pots"][f[:-4]] = {"w": im.width, "h": im.height, "soilX": ax, "soilY": ay}

    for f in sorted(x for x in os.listdir("sliced/plants_a") if x.endswith(".png")):
        im = Image.open(f"sliced/plants_a/{f}").convert("RGBA")
        ax, ay = stem_anchor(im)
        total += save(im, f"{OUT}/plants/{f[:-4]}.webp")
        meta["plants"][f[:-4]] = {"w": im.width, "h": im.height, "stemX": ax, "stemY": ay}

    for f in sorted(x for x in os.listdir("sliced/tiles") if x.endswith(".png")):
        im = fit_tile(Image.open(f"sliced/tiles/{f}").convert("RGBA"), width=312)
        w, h, thick = top_face(im)
        total += save(im, f"{OUT}/tiles/{f[:-4]}.webp")
        # 타일 윗면 한가운데 — 여기에 화분을 세웁니다
        meta["tiles"][f[:-4]] = {"w": im.width, "h": im.height,
                                 "topW": round(w), "topH": round(h),
                                 "cx": im.width // 2, "cy": round(h / 2)}

    bg = Image.open("sheets/greenhouse_bg.png").convert("RGB")
    total += save(bg, f"{OUT}/greenhouse.webp")

    os.makedirs(OUT, exist_ok=True)
    json.dump(meta, open(f"{OUT}/atlas.json", "w"), indent=1)
    n = len(meta["pots"]) + len(meta["plants"]) + len(meta["tiles"]) + 1
    print(f"{n}장  {total/1024/1024:.2f} MB")
    print(f"  화분 {len(meta['pots'])} · 식물 {len(meta['plants'])} · 타일 {len(meta['tiles'])} · 배경 1")
    print(f"  조합 {len(meta['pots']) * len(meta['plants'])}가지")


if __name__ == "__main__":
    main()
