"""구워진 접지 그림자를 걷어냅니다.

생성 이미지는 물체 아래에 옅은 회색 그림자를 함께 그립니다. 알파가 살아
있으면 반투명이라 괜찮지만, 평평하게 저장돼 오면 불투명한 흰 얼룩으로
굳어 흙 타일 위에서 드러납니다.

바깥 테두리에서 밝은 무채색 픽셀을 타고 번져 들어가 지웁니다. 흰 화분처럼
몸통이 밝은 물체는 실루엣 가장자리에 어두운 음영선이 있어 번짐이 막힙니다.
그림자는 앱에서 타일에 맞춰 다시 그리는 편이 낫습니다.

    python3 tools/deshadow.py sliced/pots_beds
"""
import os, sys
from collections import deque
from PIL import Image

CHROMA_MAX = 22    # 이보다 무채색이면 그림자 후보
MAX_EATEN = 0.15   # 이만큼 넘게 지워지면 물체를 먹은 것입니다
LADDER = (165, 180, 195, 210, 225)


def is_shadow(p, lum_min):
    r, g, b, a = p
    return a > 0 and max(r, g, b) - min(r, g, b) < CHROMA_MAX and min(r, g, b) >= lum_min


def strip(im, lum_min):
    W, H = im.size
    px = im.load()
    seen = bytearray(W * H)
    q = deque()

    def push(x, y):
        if 0 <= x < W and 0 <= y < H and not seen[y * W + x]:
            p = px[x, y]
            if p[3] == 0 or is_shadow(p, lum_min):
                seen[y * W + x] = 1
                q.append((x, y))

    for x in range(W):
        push(x, 0); push(x, H - 1)
    for y in range(H):
        push(0, y); push(W - 1, y)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            push(x + dx, y + dy)

    n = 0
    for y in range(H):
        for x in range(W):
            if seen[y * W + x] and px[x, y][3] != 0:
                px[x, y] = (0, 0, 0, 0)
                n += 1
    return n


def main(d):
    """한계선을 낮은 쪽부터 올려가며, 물체를 먹지 않는 가장 공격적인 값을 씁니다.

    흰 도자기나 시멘트처럼 몸통이 밝은 화분은 낮은 한계선에서 통째로
    지워집니다 - 그럴 때 자동으로 한 칸 올립니다."""
    for f in sorted(x for x in os.listdir(d) if x.endswith(".png")):
        p = os.path.join(d, f)
        src = Image.open(p).convert("RGBA")
        before = sum(1 for v in src.getchannel("A").get_flattened_data() if v)
        best = None
        for lum in LADDER:
            im = src.copy()
            n = strip(im, lum)
            if n / before <= MAX_EATEN:
                best = (im, n, lum)
                break
        if best is None:
            print(f"  {f[:-4]:26} 건너뜀 — 어느 한계선에서도 물체를 먹습니다")
            continue
        im, n, lum = best
        bb = im.getchannel("A").getbbox()
        if bb:
            im = im.crop(bb)
        im.save(p)
        note = "" if lum == LADDER[0] else f"   한계선 {lum} 로 올림"
        print(f"  {f[:-4]:26} 그림자 {n:6d}px  ({n / before * 100:4.1f}%){note}")


if __name__ == "__main__":
    main(sys.argv[1])
