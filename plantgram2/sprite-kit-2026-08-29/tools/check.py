"""
받은 시트가 쓸 수 있는지 검사합니다 — 자르기 전에 돌리세요.

    python3 tools/check.py sheet.png          일반 시트
    python3 tools/check.py sheet.png --gray   무채색 화분 세트

재는 것
  1) 투명 배경인가        배경이 칠해져 있으면 낱개로 못 자릅니다
  2) 몇 덩어리로 잘리는가  기대한 개수와 다르면 항목 간격이 좁은 것입니다
  3) 무채색인가 (--gray)  R=G=B가 아니면 색을 곱했을 때 틀어집니다
  4) 팔레트가 맞는가      톤 카드 색과 얼마나 떨어져 있는지
"""
from PIL import Image
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from slice import slice_sheet
import tempfile

TONE = {
    "화분 하이라이트": (0xDC, 0x64, 0x1E), "화분 기본": (0xC8, 0x50, 0x14),
    "화분 그림자": (0xA0, 0x3C, 0x14), "흙": (0x3C, 0x28, 0x14),
    "잎 밝은": (0x78, 0xBE, 0x1E), "잎 어두운": (0x32, 0x82, 0x14),
}

path = sys.argv[1]
gray = "--gray" in sys.argv
im = Image.open(path).convert("RGBA")
a = np.asarray(im)
rgb, al = a[..., :3].astype(np.int16), a[..., 3]
W, H = im.size
opaque = al > 200

print(f"{os.path.basename(path)}  {W}x{H}")

# 1) 투명 배경
edge = np.concatenate([al[0], al[-1], al[:, 0], al[:, -1]])
if (edge > 40).mean() > .3:
    print("  [실패] 배경이 칠해져 있습니다 — 낱개로 못 자릅니다.")
    print("         프롬프트에 'transparent background, no background color'를 넣고 다시 받으세요.")
else:
    print(f"  [통과] 투명 배경 (불투명 비율 {opaque.mean()*100:.0f}%)")

# 2) 덩어리 수
with tempfile.TemporaryDirectory() as td:
    n = len(slice_sheet(path, td, min_px=1500))
print(f"  덩어리 {n}개 — 기대한 항목 수와 다르면 항목 간격이 좁은 것입니다")

# 3) 무채색
if gray:
    px = rgb[opaque]
    spread = (px.max(1) - px.min(1))
    bad = (spread > 10).mean()
    if bad > .02:
        print(f"  [실패] 무채색이 아닙니다 — 픽셀 {bad*100:.1f}%에 색이 남아 있습니다 "
              f"(최대 편차 {int(spread.max())})")
        print("         'zero saturation, R=G=B for every pixel'을 추가해 다시 받으세요.")
    else:
        print(f"  [통과] 무채색 (색이 남은 픽셀 {bad*100:.2f}%)")

# 4) 팔레트 근접도
if not gray:
    px = rgb[opaque][::37]
    print("  팔레트 근접도 — 각 기준색에 가장 가까운 픽셀까지의 거리 (작을수록 톤이 맞음)")
    for name, c in TONE.items():
        d = np.sqrt(((px - np.array(c)) ** 2).sum(1)).min()
        mark = "OK " if d < 40 else "멀다"
        print(f"    {mark} {name:12s} 거리 {d:5.1f}")
