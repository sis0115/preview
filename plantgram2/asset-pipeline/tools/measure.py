"""조각 하나를 재는 일을 한 곳에 모읍니다.

지금까지 재는 법이 스크립트마다 조금씩 달라서, 같은 조각이 시트마다 다른
값으로 나왔습니다. 재는 법은 하나여야 합니다.
"""
import numpy as np
from PIL import Image
from scipy import ndimage


def cut(path, min_px=800, close=9):
    """시트에서 조각을 잘라 냅니다. 왼→오, 위→아래 차례로."""
    im = Image.open(path).convert("RGBA")
    al = np.asarray(im).astype(float)[..., 3] / 255
    solid = ndimage.binary_fill_holes(
        ndimage.binary_closing(al > .5, np.ones((close, close))))
    lab, k = ndimage.label(solid)
    out = []
    for c in range(1, k + 1):
        own = lab == c
        if own.sum() < min_px:
            continue
        ys, xs = np.nonzero(own)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        a = np.asarray(im.crop(box)).astype(float)
        a[..., 3] *= own[box[1]:box[3], box[0]:box[2]]     # 옆 조각을 데려오지 않게
        out.append((box, Image.fromarray(a.astype("uint8"), "RGBA")))
    out.sort(key=lambda p: (p[0][1] // 300, p[0][0]))
    return out


def alpha_health(art):
    """배경이 깨끗한지. 불투명한데 무채색이고 아주 밝으면 남은 배경입니다."""
    a = np.asarray(art).astype(float) / 255
    op = a[..., 3] > .9
    rgb = a[..., :3]
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    res = int((op & (sat < .03) & (mx > .93)).sum())
    return {"opaque": int(op.sum()), "residue": res,
            "residuePct": round(res / max(int(op.sum()), 1) * 100, 3)}


def base(art, grid, art_to_stage):
    """밑면. 맨 아래 꼭짓점에서 양쪽으로 몇 칸인지 - **반올림 전** 값입니다."""
    U = np.array([grid["uX"], grid["uY"]]) / art_to_stage
    V = np.array([grid["vX"], grid["vY"]]) / art_to_stage
    m = np.asarray(art).astype(float)[..., 3] / 255 > .5
    ys, xs = np.nonzero(m)
    near = xs[ys > ys.max() - 3]
    xb = (near.min() + near.max()) / 2
    L = (xb - xs.min()) / abs(U[0])
    R = (xs.max() - xb) / abs(V[0])
    step = lambda n: max(1, int(n + .75))                  # noqa: E731
    return {"spanU": round(float(L), 3), "spanV": round(float(R), 3),
            "cells": [step(L), step(R)],
            "foot": [float(xb - (L * U[0] + R * V[0]) / 2),
                     float(ys.max() - (L * U[1] + R * V[1]) / 2)],
            "top": int(ys.min())}


def plate(art, grid, art_to_stage, b):
    """윗판 위의 자리. 상자와 격자만으로 계산합니다(RULES 4.5)."""
    U = np.array([grid["uX"], grid["uY"]]) / art_to_stage
    V = np.array([grid["vX"], grid["vY"]]) / art_to_stage
    half = (b["spanU"] * abs(U[1]) + b["spanV"] * abs(V[1])) / 2
    cx, top = b["foot"][0], b["top"] + half
    axis = U if b["cells"][0] > b["cells"][1] else V
    n = max(b["cells"])
    return [[float(cx + axis[0] * (k - (n - 1) / 2)),
             float(top + axis[1] * (k - (n - 1) / 2))] for k in range(n)]


def stem(art):
    """식물 밑동. 바닥에서 위로 가장 길게 이어진 기둥의 한가운데입니다."""
    m = np.asarray(art).astype(float)[..., 3] / 255 > .5
    h, w = m.shape
    run = np.zeros(w)
    low = np.zeros(w, int)
    for x in range(w):
        ys = np.nonzero(m[:, x])[0]
        if not len(ys):
            continue
        low[x] = ys.max()
        y = ys.max()
        while y > 0 and m[y - 1, x]:
            y -= 1
        run[x] = low[x] - y
    if run.max() == 0:
        return [w / 2, h - 1]
    keep = np.nonzero(run >= run.max() * .15)[0]
    return [float((keep.min() + keep.max()) / 2), float(low[keep].max())]
