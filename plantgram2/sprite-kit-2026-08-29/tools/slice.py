"""
스프라이트 시트를 낱개로 자릅니다 — 알파 연결요소로 덩어리를 찾습니다.

    python3 tools/slice.py sheet.png out/ [최소픽셀]

생성 이미지는 배경이 투명해야 합니다. 배경이 칠해져 있으면 시트 전체가
한 덩어리가 되어 못 자릅니다 — 프롬프트에 "transparent background"를 반드시 넣으세요.

gap 만큼 팽창시킨 뒤 덩어리를 찾습니다. 잎끝처럼 안티에일리어싱으로 끊긴 부분을
한 식물로 묶기 위해서입니다. 반대로 두 식물이 너무 붙어 있으면 하나로 합쳐지므로,
시트를 만들 때 항목 사이를 넉넉히(40px 이상) 띄우도록 프롬프트에 명시합니다.
"""
from PIL import Image
import numpy as np, sys, os, json
from collections import deque

def slice_sheet(path, outdir, alpha_min=60, min_px=900, pad=6, gap=3):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im)[..., 3]
    H, W = a.shape
    # 살짝 팽창시켜 잎끝처럼 끊긴 부분을 한 덩어리로 묶습니다
    m = a > alpha_min
    d = m.copy()
    for _ in range(gap):
        d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
        m = d.copy()
    seen = np.zeros((H, W), bool); boxes = []
    for y in range(H):
        for x in range(W):
            if not d[y, x] or seen[y, x]: continue
            q = deque([(y, x)]); seen[y, x] = True
            y0 = y1 = y; x0 = x1 = x; n = 0
            while q:
                cy, cx = q.popleft(); n += 1
                if cy < y0: y0 = cy
                if cy > y1: y1 = cy
                if cx < x0: x0 = cx
                if cx > x1: x1 = cx
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = cy+dy, cx+dx
                    if 0 <= ny < H and 0 <= nx < W and d[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx))
            if n >= min_px: boxes.append((x0, y0, x1, y1))
    # 위→아래, 왼→오른 순서로 정렬 (행 단위)
    #
    # 행은 밑선(y1)으로 나눕니다. 위쪽(y0)으로 나누면 같은 줄에 있어도
    # 키 큰 성체가 윗줄로 올라가 성장 단계가 뒤집힙니다 — 실제로 겪었습니다.
    # 밑선은 한 줄 안에서 거의 같으므로 안전합니다.
    if boxes:
        base = sorted(b[3] for b in boxes)
        rows, cur = [], [base[0]]
        for v in base[1:]:
            if v - cur[-1] > 80:
                rows.append(cur)
                cur = [v]
            else:
                cur.append(v)
        rows.append(cur)
        centers = [sum(r) / len(r) for r in rows]

        def row_of(b):
            return min(range(len(centers)), key=lambda i: abs(centers[i] - b[3]))

        boxes.sort(key=lambda b: (row_of(b), b[0]))
    os.makedirs(outdir, exist_ok=True)
    meta = []
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        box = (max(0, x0-pad), max(0, y0-pad), min(W, x1+1+pad), min(H, y1+1+pad))
        im.crop(box).save(f"{outdir}/s{i:02d}.png")
        meta.append({"id": f"s{i:02d}", "box": box, "w": box[2]-box[0], "h": box[3]-box[1]})
    return meta

if __name__ == "__main__":
    out = sys.argv[2]
    meta = slice_sheet(sys.argv[1], out,
                       min_px=int(sys.argv[3]) if len(sys.argv) > 3 else 900)
    with open(f"{out}/index.json", "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(len(meta), "조각 —", out)
    for m in meta: print(" ", m["id"], f'{m["w"]}x{m["h"]}')
