"""
잘라낸 스프라이트를 앱에 넣을 형태로 변환합니다.

    python3 tools/pack.py sliced/ ../assets/ [--size 234] [--q 90]

  · 격자 한 칸이 78px이므로 @3x = 234px면 충분합니다. 그 이상은 용량만 늘어납니다.
  · WebP로 저장합니다 — 같은 화질에서 PNG의 3분의 1입니다 (실측 59KB → 21KB).
    Flutter는 WebP를 기본 지원하고 알파도 유지됩니다.
"""
from PIL import Image
import sys, os, glob, json

src, dst = sys.argv[1], sys.argv[2]
size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 234
q = int(sys.argv[sys.argv.index('--q') + 1]) if '--q' in sys.argv else 90
os.makedirs(dst, exist_ok=True)

out, total = [], 0
for f in sorted(glob.glob(f"{src}/*.png")):
    im = Image.open(f).convert("RGBA")
    im.thumbnail((size, size), Image.LANCZOS)
    # 접지점(바닥 중앙)을 함께 기록합니다 — 아이소 격자에 앉힐 때 이 점을 타일 중심에 둡니다
    bbox = im.getchannel("A").getbbox()
    name = os.path.basename(f)[:-4]
    p = f"{dst}/{name}.webp"
    im.save(p, "WEBP", quality=q)
    total += os.path.getsize(p)
    out.append({"id": name, "w": im.width, "h": im.height,
                "anchorX": round((bbox[0] + bbox[2]) / 2, 1), "anchorY": bbox[3]})

with open(f"{dst}/manifest.json", "w") as fh:
    json.dump({"size": size, "quality": q, "sprites": out}, fh, ensure_ascii=False, indent=1)
print(f"{len(out)}장 · {total // 1024} KB · 평균 {total // max(1, len(out)) // 1024} KB")
print(f"manifest.json 에 접지점(anchorX/anchorY)까지 기록했습니다")
