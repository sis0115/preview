"""무대 그림의 바닥을 우리 격자에 맞춰 다시 깝니다.

받은 그림의 칠해진 타일은 일정한 격자가 아닙니다 - 간격이 제각각이라
우리 격자를 아무리 맞춰도 두 겹으로 보입니다. 재는 대신 다시 깝니다.

소품은 건드리지 않습니다. 바닥으로 보이는 픽셀에만 덮개를 씌우므로
작업대 다리도 선반도 그대로 남습니다. 색은 그림에서 떠 오므로 뒤쪽이
밝고 앞쪽이 어두운 음영도 그대로입니다 - 우리가 새로 넣는 것은 이음선과
한 칸 걸러 들어가는 아주 옅은 명암뿐입니다.

    python3 tools/make_floor.py sheets/kit.png ../app-kit/assets
"""
import json, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def floor_mask(rgb, alpha):
    """바닥 = 채도 낮고 밝은 영역. 잔디(초록)와 유리(푸른빛)를 뺍니다."""
    a = rgb.astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (alpha > 120) & (sat < .12) & (mx > .82) & (g < r + .03) & (b < r + .03)


def main(sheet, out="../app-kit/assets", ref="sheets/kit_ref.json"):
    m = json.load(open(ref))
    st = m["stage"]
    n = st["grid"]
    T = np.array([st["topX"], st["topY"]], float)
    u = np.array([st["uX"], st["uY"]], float)
    v = np.array([st["vX"], st["vY"]], float)

    im = Image.open(sheet).convert("RGBA").crop((0, 0, st["w"], st["h"]))
    rgb = np.asarray(im.convert("RGB")).astype(float)
    A = np.asarray(im.getchannel("A"))

    h, w = A.shape
    yy, xx = np.mgrid[0:h, 0:w]
    det = u[0] * v[1] - u[1] * v[0]
    qx, qy = xx - T[0], yy - T[1]
    al = (qx * v[1] - qy * v[0]) / det
    be = (u[0] * qy - u[1] * qx) / det

    inside = (al > 0) & (al < n) & (be > 0) & (be < n)
    mask = floor_mask(rgb, A) & inside
    # 이음선 자체는 어두워서 바닥 판정에서 빠집니다. 메워 줍니다.
    mask = ndimage.binary_closing(mask, np.ones((9, 9)))
    lab, k = ndimage.label(mask)
    if k > 1:
        big = 1 + np.argmax(ndimage.sum(mask, lab, range(1, k + 1)))
        mask = lab == big
    mask = ndimage.binary_opening(mask, np.ones((5, 5))) & inside

    # 칠해진 이음선을 지운 바탕색. 중앙값이라 가는 선은 사라지고
    # 넓은 음영은 남습니다.
    base = np.stack([
        ndimage.median_filter(rgb[..., c], size=21) for c in range(3)
    ], -1)

    # 우리 이음선. 칸 경계까지의 거리를 픽셀로 환산합니다.
    stepA = abs(np.dot(u, np.array([-v[1], v[0]]) / np.hypot(*v)))
    stepB = abs(np.dot(v, np.array([-u[1], u[0]]) / np.hypot(*u)))
    da = np.minimum(al % 1, 1 - al % 1) * stepA
    db = np.minimum(be % 1, 1 - be % 1) * stepB
    d = np.minimum(da, db)

    # 선은 1.1px 폭에 0.9px 번짐. 얇고 은은하게.
    seam = np.clip(1 - (d - 1.1) / .9, 0, 1)
    checker = (np.floor(al).astype(int) + np.floor(be).astype(int)) % 2

    tile = base.copy()
    tile *= (1 - .035 * checker)[..., None]          # 한 칸 걸러 아주 옅게
    tile *= (1 - .10 * seam)[..., None]              # 이음선

    a = ndimage.binary_erosion(mask, np.ones((3, 3))).astype(float)
    a = ndimage.gaussian_filter(a, 1.1)
    a = np.clip((a - .35) / .5, 0, 1)

    plate = np.dstack([np.clip(tile, 0, 255), a * 255]).astype(np.uint8)
    img = Image.fromarray(plate, "RGBA")
    img.save(f"{out}/greenhouse/floor.png")
    print(f"{out}/greenhouse/floor.png  바닥 {int(mask.sum())}px · 격자 {n}x{n}")


if __name__ == "__main__":
    main(*sys.argv[1:])
