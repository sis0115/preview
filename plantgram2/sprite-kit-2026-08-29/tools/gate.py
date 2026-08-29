"""시트를 받아들일지 되돌려보낼지 판정합니다.

여덟 장을 받는 동안 저는 어긋난 시트를 그때그때 코드로 기웠습니다.
숫자는 맞았지만 그림은 안 맞았습니다. 기우지 말고, 기준에 못 미치면
다시 받아야 합니다. 그 기준을 여기 박아 둡니다.

기준값은 레퍼런스 게임 이미지에서 실측한 것입니다.

    python3 tools/gate.py sheets/tiles.png --iso
"""
import sys
import numpy as np
from PIL import Image

# 레퍼런스 실측: 채도 0.279 · 명도 0.781 · 명암 폭 0.178
SAT = (0.20, 0.38)
VAL = (0.68, 0.86)
CONTRAST = (0.13, 0.26)
ISO = (1.50, 1.80)      # 바닥 마름모 가로 ÷ 세로


def tone(im):
    a = np.asarray(im.convert("RGB")).astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    keep = ~((mn > .93) & (sat < .06))          # 흰 여백 제외
    if not keep.any():
        return 0.0, 0.0, 0.0
    return sat[keep].mean(), mx[keep].mean(), mx[keep].std()


def iso_ratio(im):
    """가장 큰 덩어리의 윗면 마름모 비율. 바닥·타일 시트에만 씁니다."""
    a = np.asarray(im.convert("RGBA").getchannel("A")) > 40
    if not a.any():
        return None
    ys, xs = np.nonzero(a)
    x0, x1 = xs.min(), xs.max()
    vy = (ys[xs == x0].min() + ys[xs == x1].min()) / 2
    top_h = (vy - ys.min()) * 2
    return (x1 - x0) / top_h if top_h > 0 else None


def row(label, value, lo, hi, fmt="{:.3f}"):
    ok = lo <= value <= hi
    mark = "통과" if ok else "탈락"
    print(f"  [{mark}] {label:10} {fmt.format(value):>7}   기준 {fmt.format(lo)}~{fmt.format(hi)}")
    return ok


def main(path, check_iso):
    im = Image.open(path)
    print(f"{path.split('/')[-1]}  {im.width}x{im.height}")
    sat, val, con = tone(im)
    ok = row("채도", sat, *SAT)
    ok &= row("명도", val, *VAL)
    ok &= row("명암 폭", con, *CONTRAST)
    if check_iso:
        r = iso_ratio(im)
        if r is None:
            print("  [탈락] 등각 비율    잴 수 없음 — 알파가 없습니다")
            ok = False
        else:
            ok &= row("등각 비율", r, *ISO, fmt="{:.2f}")
    print("\n" + ("→ 받아들입니다." if ok
                  else "→ 되돌려보냅니다. 코드로 기우지 말고 다시 받으세요."))
    return 0 if ok else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0], "--iso" in sys.argv))
