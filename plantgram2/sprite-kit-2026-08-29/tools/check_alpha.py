"""잘라 낸 조각에 배경이 남아 있는지 셉니다.

배경(체커보드)이 그려져 온 시트를 뜯어내면 좁은 틈에 흰 픽셀이 남습니다.
다만 하얀 것이 모두 잔재는 아닙니다 - 시멘트 화분은 원래 희고, 잎에도
밝은 무늬가 있습니다. 채도로 가릅니다.

  채도 0.03 아래 · 아주 밝음  → 배경 잔재
  채도 0.03~0.10             → 그림 자체의 밝은 색

    python3 tools/check_alpha.py ../app-kit/assets
"""
import json, sys
import numpy as np
from PIL import Image


def stats(path):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im.getchannel("A")).astype(float) / 255
    rgb = np.asarray(im.convert("RGB")).astype(float) / 255
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    solid = (a > .6)
    residue = solid & (sat < .03) & (mx > .94)
    return int(solid.sum()), int(residue.sum())


def main(assets="../app-kit/assets"):
    cat = json.load(open(f"{assets}/catalog.json"))
    items = ([(f"{assets}/pots/{k}.png", k) for k in cat["pots"]]
             + [(f"{assets}/plants/{k}.png", k) for k in cat["plants"]])
    bad = 0
    print(f"{'조각':14} {'불투명':>8} {'배경 잔재':>9} {'비율':>7}   판정")
    for path, name in items:
        solid, res = stats(path)
        r = res / max(solid, 1)
        ok = r <= .003
        bad += 0 if ok else 1
        print(f"{name:14} {solid:8} {res:9} {r:7.2%}   "
              + ("깨끗" if ok else "← 배경이 남았습니다"))
    print(f"\n{len(items) - bad}/{len(items)} 깨끗")
    if bad:
        print("남은 조각은 좁은 틈에 배경이 끼어 있습니다. "
              "다음 시트는 마젠타 단색 배경으로 받으세요(RULES 11.7).")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
