// 이미지 없이 코드로만 그리는 방식의 예제.
//
// 스프라이트를 한 장도 쓰지 않습니다. 타일도 화분도 잎도 전부 Path 로
// 그립니다. 그래서 종·단계·색을 숫자로 바꾸면 그림이 따라 바뀝니다.

import 'dart:math' as math;

import 'package:flutter/material.dart';

void main() => runApp(const DrawDemo());

// ── 톤 ──────────────────────────────────────────────────────
// 기존 앱 화면에서 실측한 값에 맞춥니다: 채도 0.09 · 명도 0.89.
// 연하고 밝게. 진한 색을 쓰면 혼자 튑니다.
const _leafLit = Color(0xFFC3DCB4);
const _leafDim = Color(0xFF87AC79);
const _stem = Color(0xFF8FB07E);
const _potMid = Color(0xFFDCBCA1);
const _soil = Color(0xFF9C8571);
const _tileTop = Color(0xFFF0EBE0);
const _ground = Color(0xFFF7F4EC);

// ── 등각 규격 ────────────────────────────────────────────────
// 바닥 마름모는 가로:세로 1.64:1. 앱 화면에서 실측한 각도입니다.
const double kTileW = 156;
const double kTileH = kTileW / 1.64;

/// 격자 좌표 (i, j) 와 높이 z 를 화면 좌표로.
Offset iso(double i, double j, [double z = 0]) =>
    Offset((i - j) * kTileW / 2, (i + j) * kTileH / 2 - z);

/// 중심과 반지름으로 등각 타원 하나. 화분 테두리·흙 윗면에 씁니다.
Rect isoOval(Offset c, double r) =>
    Rect.fromCenter(center: c, width: r * 2, height: r * 2 / 1.64);

// ── 타일 ────────────────────────────────────────────────────

/// 마름모 윗면 + 앞쪽 옆면. 두께는 윗면 높이의 8% 를 넘기지 않습니다.
void drawTile(Canvas canvas, Offset at, Color top, {double thick = 7}) {
  final hw = kTileW / 2, hh = kTileH / 2;
  final face = Path()
    ..moveTo(at.dx, at.dy - hh)
    ..lineTo(at.dx + hw, at.dy)
    ..lineTo(at.dx, at.dy + hh)
    ..lineTo(at.dx - hw, at.dy)
    ..close();

  final side = Path()
    ..moveTo(at.dx - hw, at.dy)
    ..lineTo(at.dx, at.dy + hh)
    ..lineTo(at.dx + hw, at.dy)
    ..lineTo(at.dx + hw, at.dy + thick)
    ..lineTo(at.dx, at.dy + hh + thick)
    ..lineTo(at.dx - hw, at.dy + thick)
    ..close();

  canvas.drawPath(side, Paint()..color = _shade(top, .88));
  canvas.drawPath(face, Paint()..color = top);
}

Color _shade(Color c, double k) => Color.fromARGB(
  (c.a * 255).round(),
  (c.r * 255 * k).round().clamp(0, 255),
  (c.g * 255 * k).round().clamp(0, 255),
  (c.b * 255 * k).round().clamp(0, 255),
);

// ── 화분 ────────────────────────────────────────────────────

/// 위가 넓고 아래가 좁은 화분. 뒤 테두리 → 몸통 → 흙 → 앞 테두리 순서로
/// 그려야 흙이 화분 안에 담긴 것처럼 보입니다.
void drawPot(
  Canvas canvas,
  Offset base, {
  required double rTop,
  required double height,
  Color body = _potMid,
}) {
  final rBot = rTop * .74;
  final top = base.translate(0, -height);

  // 몸통 — 위 테두리 양끝에서 아래 테두리 양끝으로
  final wall = Path()
    ..moveTo(top.dx - rTop, top.dy)
    ..lineTo(base.dx - rBot, base.dy)
    ..arcTo(isoOval(base, rBot), math.pi, -math.pi, false)
    ..lineTo(top.dx + rTop, top.dy)
    ..arcTo(isoOval(top, rTop), 0, -math.pi, false)
    ..close();
  canvas.drawPath(wall, Paint()..color = body);

  // 오른쪽 아래가 그늘. 광원은 왼쪽 위 하나로 고정합니다.
  canvas.save();
  canvas.clipPath(wall);
  canvas.drawPath(
    Path()
      ..moveTo(top.dx + rTop * .1, top.dy)
      ..lineTo(base.dx + rBot, base.dy + rBot)
      ..lineTo(top.dx + rTop * 1.2, top.dy + height)
      ..close(),
    Paint()..color = _shade(body, .9),
  );
  canvas.restore();

  // 흙, 그리고 그 위를 덮는 앞쪽 테두리
  canvas.drawOval(isoOval(top, rTop * .88), Paint()..color = _soil);
  final rim = Paint()
    ..style = PaintingStyle.stroke
    ..strokeWidth = rTop * .13
    ..color = _shade(body, 1.06);
  canvas.drawArc(isoOval(top, rTop * .94), 0, math.pi, false, rim);
}

// ── 잎 ──────────────────────────────────────────────────────

/// 잎 한 장. 중심선을 그리고 좌우로 폭을 벌려 닫습니다.
///
/// 여기서 잎마다 [len]·[wid]·[bend]·[tilt] 를 다르게 주는 것이 핵심입니다.
/// 한 장을 만들어 복제하면 아무리 많이 붙여도 조화롭게 보이지 않습니다.
Path leafPath({
  required double len,
  required double wid,
  required double bend,
}) {
  final path = Path()..moveTo(0, 0);
  // 오른쪽 가장자리
  path.cubicTo(wid * .9, -len * .22, wid, -len * .62, bend * .5, -len);
  // 왼쪽 가장자리로 되돌아옵니다
  path.cubicTo(-wid + bend, -len * .62, -wid * .9, -len * .22, 0, 0);
  path.close();
  return path;
}

void drawLeaf(
  Canvas canvas,
  Offset from, {
  required double len,
  required double wid,
  required double bend,
  required double tilt,
  required double lit,
}) {
  canvas.save();
  canvas.translate(from.dx, from.dy);
  canvas.rotate(tilt);
  // 등각이라 세로로 눌러 보입니다
  canvas.scale(1, .82);

  final blade = leafPath(len: len, wid: wid, bend: bend);
  final base = Color.lerp(_leafDim, _leafLit, lit)!;
  canvas.drawPath(blade, Paint()..color = base);

  // 잎의 오른쪽 절반만 한 톤 어둡게 — 면이 두 개로 읽힙니다
  canvas.save();
  canvas.clipPath(blade);
  canvas.drawPath(
    Path()
      ..moveTo(0, 0)
      ..cubicTo(wid * .9, -len * .22, wid, -len * .62, bend * .5, -len)
      ..lineTo(wid * 1.4, -len)
      ..lineTo(wid * 1.4, 0)
      ..close(),
    Paint()..color = _shade(base, .93),
  );
  canvas.restore();

  // 잎맥 하나. 이 크기에서는 하나면 충분합니다.
  canvas.drawPath(
    Path()
      ..moveTo(0, 0)
      ..quadraticBezierTo(bend * .25, -len * .5, bend * .5, -len * .94),
    Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = math.max(1, wid * .07)
      ..color = _shade(base, .92),
  );
  canvas.restore();
}

// ── 식물 ────────────────────────────────────────────────────

enum Species { broadleaf, fan, cane }

/// 종과 단계로 식물 한 그루. 그림이 아니라 규칙입니다.
void drawPlant(
  Canvas canvas,
  Offset soil, {
  required Species species,
  required int stage, // 1..4
  required int seed,
}) {
  final rnd = math.Random(seed);
  final t = stage / 4;
  final n = switch (species) {
    Species.broadleaf => (1 + stage * 1.6).round(),
    Species.fan => (2 + stage * 1.4).round(),
    Species.cane => (1 + stage).round(),
  };
  final scale = .35 + .65 * t;

  if (species == Species.cane) {
    // 대나무 — 줄기를 세우고 마디마다 옆으로 잎을 냅니다
    for (var k = 0; k < n; k++) {
      final dx = (k - (n - 1) / 2) * 9 * scale + rnd.nextDouble() * 4 - 2;
      final h = (58 + rnd.nextDouble() * 26) * scale;
      final foot = soil.translate(dx, -2.0);
      canvas.drawLine(
        foot,
        foot.translate(0, -h),
        Paint()
          ..strokeWidth = 4.6 * scale
          ..strokeCap = StrokeCap.round
          ..color = _stem,
      );
      final nodes = 2 + stage;
      for (var m = 1; m <= nodes; m++) {
        final y = foot.dy - h * (m / (nodes + .4));
        final side = m.isEven ? 1 : -1;
        drawLeaf(
          canvas,
          Offset(foot.dx, y),
          len: (16 + rnd.nextDouble() * 9) * scale,
          wid: 3.6 * scale,
          bend: 5.0 * side,
          tilt: side * (1.05 + rnd.nextDouble() * .5),
          lit: .3 + rnd.nextDouble() * .6,
        );
      }
    }
    return;
  }

  // 근생형 — 흙에서 바로 잎이 벌어져 나옵니다
  final spread = species == Species.fan ? 1.05 : .78;
  for (var k = 0; k < n; k++) {
    final u = n == 1 ? .5 : k / (n - 1);
    final tilt = (u - .5) * 2 * spread + (rnd.nextDouble() - .5) * .16;
    final grow = .78 + rnd.nextDouble() * .42; // 잎마다 길이를 흔듭니다
    final len = (species == Species.fan ? 62.0 : 46.0) * scale * grow;
    final wid = (species == Species.fan ? 11.0 : 17.0) * scale * grow;
    // 줄기
    canvas.save();
    canvas.translate(soil.dx, soil.dy - 2);
    canvas.rotate(tilt);
    canvas.scale(1, .82);
    canvas.drawLine(
      Offset.zero,
      Offset(0, -len * .34),
      Paint()
        ..strokeWidth = 2.6 * scale
        ..strokeCap = StrokeCap.round
        ..color = _stem,
    );
    canvas.restore();
    drawLeaf(
      canvas,
      soil.translate(0, -2),
      len: len,
      wid: wid,
      bend: (rnd.nextDouble() - .5) * wid * 1.1,
      tilt: tilt,
      // 왼쪽 위 광원 — 왼쪽으로 기운 잎이 밝습니다
      lit: (.5 - tilt * .55).clamp(0.0, 1.0),
    );
  }
}

// ── 화면 ────────────────────────────────────────────────────

class DrawDemo extends StatelessWidget {
  const DrawDemo({super.key});

  @override
  Widget build(BuildContext context) => const MaterialApp(
    debugShowCheckedModeBanner: false,
    home: Scaffold(
      backgroundColor: _ground,
      body: Center(child: CustomPaint(size: Size(980, 620), painter: _Demo())),
    ),
  );
}

class _Demo extends CustomPainter {
  const _Demo();

  @override
  void paint(Canvas canvas, Size size) {
    canvas.translate(size.width / 2, 150);

    const plan = [
      (Species.broadleaf, 0),
      (Species.fan, 1),
      (Species.cane, 2),
    ];

    // 뒤에서 앞으로. (i + j) 오름차순이면 앞쪽이 뒤쪽을 가립니다.
    final cells = [
      for (var i = 0; i < 3; i++)
        for (var j = 0; j < 4; j++) (i, j),
    ]..sort((a, b) => (a.$1 + a.$2).compareTo(b.$1 + b.$2));

    for (final (i, j) in cells) {
      final at = iso(i.toDouble(), j.toDouble());
      drawTile(canvas, at, (i + j).isEven ? _tileTop : _shade(_tileTop, .97));
      final (species, row) = plan[i];
      final stage = j + 1;
      drawPot(canvas, at.translate(0, 4), rTop: 21, height: 25);
      drawPlant(
        canvas,
        at.translate(0, -21),
        species: species,
        stage: stage,
        seed: row * 10 + stage,
      );
    }
  }

  @override
  bool shouldRepaint(_Demo old) => false;
}
