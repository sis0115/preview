"""판 있는 가구의 자리를 상자와 격자만으로 되돌려 읽습니다(RULES 4.5).

판을 눈으로 찾아 나서지 않습니다. 조각의 맨 위 점이 윗판 윗면의 먼
꼭짓점이고, 윗면은 밑면과 같은 평행사변형이므로 거기서 반 칸 내려오면
윗면 한가운데입니다. 자리는 덮은 칸들의 한가운데를 그 높이로 올린 점.

아래층 판은 상자만으로는 높이를 알 수 없어 자리를 두지 않습니다.
모르는 것은 모른다고 두고, 아는 것만 씁니다.
"""
import numpy as np


def base_span(art, grid, art_to_stage):
    """밑면이 두 축으로 몇 칸인지. **반올림하지 않은** 값입니다.

    칸 수는 자리를 잡을 때 반올림하지만, 판 높이를 잴 때는 반올림하면
    안 됩니다. 선반은 밑면이 1.87 칸인데 2 로 올려서 재면 판이 31px
    아래로 내려가, 화분이 판을 뚫고 가라앉습니다.
    """
    U = np.array([grid["uX"], grid["uY"]]) / art_to_stage
    V = np.array([grid["vX"], grid["vY"]]) / art_to_stage
    m = np.asarray(art.convert("RGBA")).astype(float)[..., 3] / 255 > .5
    ys, xs = np.nonzero(m)
    near = xs[ys > ys.max() - 3]
    xb = (near.min() + near.max()) / 2
    return ((xb - xs.min()) / abs(U[0]), (xs.max() - xb) / abs(V[0]))


def plate_slots(art, cells, grid, art_to_stage, foot_x, span=None):
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

    # 윗면은 밑면과 **같은 크기**의 평행사변형입니다. 반올림한 칸 수가
    # 아니라 실제로 잰 밑면으로 반 칸을 구해야 판 위에 정확히 앉습니다.
    L, R = span if span is not None else base_span(art, grid, art_to_stage)
    half = (L * abs(U[1]) + R * abs(V[1])) / 2
    cx = foot_x
    top = ys.min() + half                       # 윗면 한가운데의 화면 높이

    axis = U if cells[0] > cells[1] else V
    n = max(cells)
    return [(float(cx + axis[0] * (k - (n - 1) / 2)),
             float(top + axis[1] * (k - (n - 1) / 2))) for k in range(n)]
