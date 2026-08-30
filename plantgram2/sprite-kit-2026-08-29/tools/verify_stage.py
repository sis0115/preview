"""돌아온 배경의 바닥에서 격자를 읽습니다.

바깥 꼭짓점을 그냥 재면 안 됩니다 - 뒤쪽 두 꼭짓점은 유리에 가려 있고,
바닥 가장자리의 두꺼운 턱까지 딸려 옵니다(예전에 31.9px 어긋났습니다).

앞쪽 두 변만 봅니다. 여기는 아무것도 가리지 않습니다.
  · 두 변에 직선을 맞춰 기울기를 얻고
  · 둘의 교점이 앞 꼭짓점
  · 마스크의 좌우 끝이 좌우 꼭짓점
  · 뒤 꼭짓점은 평행사변형이므로 왼 + 오 - 앞

두 변의 기울기가 서로 맞고 |u| 와 |v| 가 같으면 믿을 만한 읽기입니다.
어긋나면 다시 받습니다.

    python3 tools/verify_stage.py sheets/stage.png sheets/stage_guide.json
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def floor_mask(rgb):
    """바닥 = 채도 낮고 아주 밝고 살짝 따뜻한 색. 잔디·유리·하늘을 뺍니다."""
    a = rgb.astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    m = (sat < .12) & (mx > .86) & (a[..., 2] < a[..., 0] - .005)
    m = ndimage.binary_opening(m, np.ones((21, 21)))   # 가는 창틀을 끊습니다
    lab, k = ndimage.label(m)
    if k == 0:
        return m
    return lab == 1 + int(np.argmax(ndimage.sum(m, lab, range(1, k + 1))))


def read_grid(mask, n):
    h, w = mask.shape
    low = np.full(w, -1)
    for x in range(w):
        ys = np.nonzero(mask[:, x])[0]
        if len(ys):
            low[x] = ys.max()
    cols = np.nonzero(low >= 0)[0]
    apex = int(cols[np.argmax(low[cols])])

    def fit(sel):
        return np.polyfit(sel, low[sel], 1)

    a = cols[(cols > cols.min() + 30) & (cols < apex - 40)]
    b = cols[(cols > apex + 40) & (cols < cols.max() - 30)]
    sl, sr = fit(a), fit(b)
    bx = (sr[1] - sl[1]) / (sl[0] - sr[0])
    B = np.array([bx, sl[0] * bx + sl[1]])
    L = np.array([cols.min(), sl[0] * cols.min() + sl[1]])
    R = np.array([cols.max(), sr[0] * cols.max() + sr[1]])
    T = L + R - B
    return dict(T=T, L=L, R=R, B=B, u=(R - T) / n, v=(L - T) / n,
                slopeL=sl[0], slopeR=sr[0])


# 이음선에 맞춰 위상까지 밀어 보았지만 더 어긋났습니다. 어두운 정도에는
# 이음선만이 아니라 타일마다의 음영도 섞여 있어 위상이 흔들립니다.
# 앞변에서 얻은 격자가 이미 5px 안쪽이라 그대로 씁니다.


def main(art, spec_path="sheets/stage_guide.json", out=None):
    out = out or "sheets/stage_check.png"
    spec = json.load(open(spec_path))
    im = Image.open(art).convert("RGB")
    if im.size != (spec["width"], spec["height"]):
        print(f"크기가 다릅니다: {im.size} — 다시 받아야 합니다")
        return 1

    n = spec["n"]
    rgbv = np.asarray(im)
    g = read_grid(floor_mask(rgbv), n)
    u, v = g["u"], g["v"]
    tw = abs(u[0]) + abs(v[0])
    th = u[1] + v[1]

    print(f"앞변 기울기   왼 {g['slopeL']:+.4f}   오 {g['slopeR']:+.4f}"
          f"   (서로 {abs(abs(g['slopeL']) - abs(g['slopeR'])):.4f} 차이)")
    print(f"칸 벡터       u {u.round(1)}  |u| {np.hypot(*u):.1f}")
    print(f"              v {v.round(1)}  |v| {np.hypot(*v):.1f}")
    print(f"타일          {tw:.1f} x {th:.1f}   등각비 {tw / th:.2f} : 1")
    print(f"우리가 요청   {spec['tileW']} x {spec['tileH']}   등각비 "
          f"{spec['tileW'] / spec['tileH']:.2f} : 1")

    even = abs(np.hypot(*u) - np.hypot(*v)) / np.hypot(*u)
    tilt = abs(abs(g["slopeL"]) - abs(g["slopeR"]))
    ok = even < .03 and tilt < .02
    print(f"\n좌우 대칭 {even * 100:.1f}% · 기울기 차이 {tilt:.4f}"
          + ("   → 믿을 만한 읽기입니다" if ok else "   → 읽기가 흔들립니다"))

    dr = ImageDraw.Draw(im)
    T = g["T"]
    for i in range(n):
        for j in range(n):
            o = T + u * i + v * j
            q = [o, o + u, o + u + v, o + v]
            dr.polygon([tuple(p) for p in q], outline=(232, 106, 30))
            c = T + u * (i + .5) + v * (j + .5)
            dr.ellipse([c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3],
                       fill=(232, 106, 30))
    for p, name in ((g["T"], "위"), (g["R"], "오"), (g["B"], "아"), (g["L"], "왼")):
        dr.ellipse([p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8],
                   outline=(30, 80, 200), width=3)
    im.save(out)

    grid = {"tileW": round(tw, 1), "tileH": round(th, 1), "n": n,
            "topX": round(T[0], 1), "topY": round(T[1], 1),
            "uX": round(u[0], 2), "uY": round(u[1], 2),
            "vX": round(v[0], 2), "vY": round(v[1], 2),
            "sceneW": spec["width"], "sceneH": spec["height"]}
    json.dump(grid, open(spec_path.replace("_guide", "_grid"), "w"),
              indent=1, ensure_ascii=False)
    print(f"\n{out} — 주황 = 읽어 낸 격자, 파랑 = 바닥 네 꼭짓점")
    print(f"{spec_path.replace('_guide', '_grid')} 에 격자를 적었습니다")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
