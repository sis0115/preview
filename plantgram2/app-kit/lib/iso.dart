import 'package:flutter/material.dart';

import 'catalog.dart';

@immutable
class Cell {
  const Cell(this.i, this.j);

  final int i;
  final int j;

  /// 뒤에서 앞으로 그리는 순서. 작을수록 뒤입니다.
  int get depth => i + j;

  @override
  bool operator ==(Object o) => o is Cell && o.i == i && o.j == j;

  @override
  int get hashCode => Object.hash(i, j);

  @override
  String toString() => '($i,$j)';
}

/// 칸 좌표와 온실 그림 안의 픽셀 좌표를 오갑니다.
///
/// 바닥 마름모의 뒤쪽 꼭짓점과 두 방향 벡터로 정의합니다. 칸 한가운데는
/// 꼭짓점에서 반 칸 안쪽이라 (i + 0.5), (j + 0.5) 를 씁니다 — 이걸 빼먹으면
/// 격자가 통째로 반 칸 밀립니다.
class IsoGrid {
  const IsoGrid(this.spec);

  final GridSpec spec;

  int get size => spec.size;

  Offset center(Cell c) => spec.top + spec.u * (c.i + .5) + spec.v * (c.j + .5);

  /// 방향에 따라 바뀐 칸 수.
  ///
  /// 등각에서 **좌우로 뒤집는 것이 곧 90도 돌리는 것**입니다. 그림의 긴
  /// 축은 오른쪽 위(-v)로 뻗는데, 뒤집으면 왼쪽 위(-u)로 뻗습니다. 그래서
  /// 그림을 새로 그릴 필요 없이 뒤집고 칸 수를 맞바꾸면 됩니다.
  static List<int> turned(List<int> cells, int rot) =>
      rot == 0 ? cells : [cells[1], cells[0]];

  /// [at] 을 **맨 앞** 칸으로 삼아 뒤로 뻗는 칸들.
  static List<Cell> footprint(Cell at, List<int> cells, [int rot = 0]) {
    final c = turned(cells, rot);
    return [
      for (var di = 0; di < c[0]; di++)
        for (var dj = 0; dj < c[1]; dj++) Cell(at.i - di, at.j - dj),
    ];
  }

  /// 여러 칸에 걸친 조각이 놓이는 점. 덮은 칸들의 한가운데입니다.
  Offset anchor(Cell at, List<int> cells, [int rot = 0]) {
    final cs = footprint(at, cells, rot);
    var sum = Offset.zero;
    for (final c in cs) {
      sum += center(c);
    }
    return sum / cs.length.toDouble();
  }

  /// 화면 좌표가 떨어지는 칸. 2x2 연립방정식을 풉니다.
  Cell cellAt(Offset p) {
    final d = spec.u.dx * spec.v.dy - spec.u.dy * spec.v.dx;
    if (d == 0) return const Cell(0, 0);
    final q = p - spec.top;
    final a = (q.dx * spec.v.dy - q.dy * spec.v.dx) / d;
    final b = (spec.u.dx * q.dy - spec.u.dy * q.dx) / d;
    return Cell((a - .5).round(), (b - .5).round());
  }

  bool contains(Cell c) => c.i >= 0 && c.j >= 0 && c.i < size && c.j < size;

  Cell clamp(Cell c) => Cell(c.i.clamp(0, size - 1), c.j.clamp(0, size - 1));

  Path diamond(Cell c) {
    final o = spec.top + spec.u * c.i.toDouble() + spec.v * c.j.toDouble();
    final path = Path()..moveTo(o.dx, o.dy);
    for (final p in [o + spec.u, o + spec.u + spec.v, o + spec.v]) {
      path.lineTo(p.dx, p.dy);
    }
    return path..close();
  }

  Iterable<Cell> get cells sync* {
    for (var i = 0; i < size; i++) {
      for (var j = 0; j < size; j++) {
        yield Cell(i, j);
      }
    }
  }
}
