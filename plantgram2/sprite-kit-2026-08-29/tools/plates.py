"""판 있는 가구의 자리를 상자와 격자만으로 되돌려 읽습니다(RULES 4.5).

판을 눈으로 찾아 나서지 않습니다. 조각의 맨 위 점이 윗판 윗면의 먼
꼭짓점이고, 윗면은 밑면과 같은 평행사변형이므로 거기서 반 칸 내려오면
윗면 한가운데입니다. 자리는 덮은 칸들의 한가운데를 그 높이로 올린 점.

아래층 판은 상자만으로는 높이를 알 수 없어 자리를 두지 않습니다.
모르는 것은 모른다고 두고, 아는 것만 씁니다.
"""
import numpy as np


def plate_slots(art, cells, grid, art_to_stage, foot_x):
    """윗판 위의 자리들.

    [cells] 는 (u 쪽, v 쪽) 칸 수, [foot_x] 는 **밑면 한가운데**의 가로
    위치입니다. 맨 아래 꼭짓점을 쓰면 안 됩니다 - 밑면이 한 칸짜리가 아니면
    꼭짓점과 한가운데가 다릅니다. 2 x 1 조각에서는 39px 어긋나, 자리가
    판 밖으로 나갑니다.
    """
    U = np.array([grid["uX"], grid["uY"]]) / art_to_stage
    V = np.array([grid["vX"], grid["vY"]]) / art_to_stage
    m = np.asarray(art.convert("RGBA")).astype(float)[..., 3] / 255 > .5
    ys, _ = np.nonzero(m)

    half = (cells[0] * abs(U[1]) + cells[1] * abs(V[1])) / 2
    cx = foot_x
    top = ys.min() + half                       # 윗면 한가운데의 화면 높이

    axis = U if cells[0] > cells[1] else V
    n = max(cells)
    return [(float(cx + axis[0] * (k - (n - 1) / 2)),
             float(top + axis[1] * (k - (n - 1) / 2))) for k in range(n)]
