"""스프라이트를 기존 앱 톤에 맞춰 연하게 만듭니다.

기존 앱의 온실은 채도 0.087 · 명도 0.894 입니다. 우리 식물은 채도 0.549,
타일은 명도 0.210 이라 한 화면에 놓으면 스티커를 붙인 것처럼 겉돕니다.

채도를 낮추고 명도를 올려 맞춥니다. 흑백으로 만드는 게 아니라, 색을
흰빛 쪽으로 당기는 것입니다.

    python3 tools/grade.py sliced/plants_a out/plants --sat .30 --val .74
"""
import os, sys
import numpy as np
from PIL import Image


def measure(a, alpha):
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    m = alpha > .4
    if not m.any():
        return 0.0, 0.0
    return sat[m].mean(), mx[m].mean()


def grade(im, sat_to, val_to):
    """채도와 명도의 평균이 목표에 닿도록 전체를 같은 비율로 옮깁니다."""
    arr = np.asarray(im.convert("RGBA")).astype(float) / 255
    rgb, alpha = arr[..., :3], arr[..., 3]
    s0, v0 = measure(rgb, alpha)
    if s0 == 0 or v0 == 0:
        return im

    mx = rgb.max(2, keepdims=True)
    # 채도 낮추기 = 각 픽셀을 자기 명도의 회색 쪽으로 당깁니다
    k = min(1.0, sat_to / s0)
    rgb = mx - (mx - rgb) * k
    # 명도 올리기 = 흰색 쪽으로 당깁니다 (곱하면 색이 탁해집니다)
    v1 = measure(rgb, alpha)[1]
    if v1 > 0 and val_to > v1:
        w = min(.92, (val_to - v1) / max(1e-6, 1 - v1))
        rgb = rgb + (1 - rgb) * w

    out = np.concatenate([np.clip(rgb, 0, 1), alpha[..., None]], axis=2)
    return Image.fromarray((out * 255).round().astype(np.uint8), "RGBA")


def flatten_tile(im, keep=0.30):
    """타일 옆면 두께를 줄입니다.

    기존 앱 바닥은 얇고 평평합니다. 우리 타일은 옆면이 윗면 높이의 절반쯤
    돼서 혼자 두툼한 덩어리로 보입니다. 아래쪽을 잘라 얇게 만듭니다.
    """
    a = np.asarray(im.getchannel("A")) > 40
    ys, xs = np.nonzero(a)
    x0, x1 = xs.min(), xs.max()
    top = ys.min()
    vy = (ys[xs == x0].min() + ys[xs == x1].min()) / 2   # 좌·우 꼭짓점
    face_bottom = 2 * vy - top                            # 윗면 아래 꼭짓점
    thick = ys.max() - face_bottom                        # 그 아래가 옆면
    if thick <= 2:
        return im
    return im.crop((0, 0, im.width, round(face_bottom + thick * keep) + 1))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    sat = float(sys.argv[sys.argv.index("--sat") + 1]) if "--sat" in sys.argv else .30
    val = float(sys.argv[sys.argv.index("--val") + 1]) if "--val" in sys.argv else .74
    thin = "--thin" in sys.argv
    os.makedirs(dst, exist_ok=True)
    for f in sorted(x for x in os.listdir(src) if x.endswith(".png")):
        im = Image.open(f"{src}/{f}").convert("RGBA")
        im = grade(im, sat, val)
        if thin:
            im = flatten_tile(im)
        im.save(f"{dst}/{f}")
    print(f"{len(os.listdir(dst))}장 → {dst}  (채도 {sat} · 명도 {val}{' · 얇게' if thin else ''})")


if __name__ == "__main__":
    main()
