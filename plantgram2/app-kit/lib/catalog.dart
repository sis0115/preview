import 'dart:convert';
import 'dart:ui' as ui;

import 'package:flutter/services.dart';

/// 화분에 식물을 심는 자리 하나.
///
/// 긴 화단은 자리가 둘입니다. 등각이라 앞쪽 자리가 뒤쪽보다 아래에
/// 있으므로, 좌표를 각각 들고 있어야 두 그루가 나란히 앉습니다.
class Slot {
  const Slot(this.x, this.y, this.width);

  final double x;
  final double y;

  /// 흙의 폭. 그림자를 여기에 맞춥니다.
  final double width;

  Offset get offset => Offset(x, y);
}

class PotAsset {
  const PotAsset({
    required this.id,
    required this.size,
    required this.slots,
    required this.span,
    required this.foot,
    required this.shadow,
  });

  final String id;
  final Size size;
  final List<Slot> slots;

  /// 이 화분이 덮는 칸들. 기준 칸에서 (i, j) 로 얼마나 떨어졌는지입니다.
  ///
  /// 둥근 화분은 한 칸, 긴 화단은 두 칸입니다. 심는 자리와 순서를 맞춰
  /// 둡니다 — 첫 자리가 첫 칸에 심깁니다.
  final List<(int, int)> span;

  /// 그림 안에서 화분이 바닥에 닿는 자리. 이 점을 칸 한가운데에 놓습니다.
  ///
  /// 흙이 아니라 닿는 자리입니다. 흙을 칸에 맞추면 흙은 화분 위쪽이라
  /// 키가 큰 화단일수록 다리가 제 칸보다 한참 앞으로 나갑니다.
  final Offset foot;

  final ShadowAsset shadow;

  String get path => 'assets/pots/$id.png';

  /// 화분 그림 자체의 배율.
  ///
  /// 시트에는 화단이 둥근 화분과 비슷한 크기로 그려져 있습니다. 그대로
  /// 얹으면 두 칸짜리 화단이 한 칸도 못 채웁니다 — 재어 보니 0.59칸이었습니다.
  /// 그림에 그려진 심는 자리 사이 거리를, 실제 칸 사이 거리에 맞춰 늘립니다.
  /// 배율을 손으로 정하지 않고 격자에서 끌어내므로, 격자를 바꿔도 따라옵니다.
  double spriteScale(GridSpec g) {
    if (slots.length < 2 || span.length < 2) return 1;
    final art = (slots.last.offset - slots.first.offset).distance * g.unit;
    if (art == 0) return 1;
    final (ai, aj) = span.first;
    final (bi, bj) = span.last;
    final step = g.u * (bi - ai).toDouble() + g.v * (bj - aj).toDouble();
    return step.distance / art;
  }

  /// 자리 하나에 심는 식물의 크기 배율.
  ///
  /// 자리가 기준 흙보다 좁을 때만 줄입니다. 넓다고 키우지는 않습니다 —
  /// 같은 종이 화분에서와 화단에서 다른 크기로 자라면 어색합니다.
  double plantScale(Slot slot, double referenceSoilWidth, GridSpec g) {
    final w = slot.width * spriteScale(g);
    return w < referenceSoilWidth ? w / referenceSoilWidth : 1;
  }
}

class PlantAsset {
  const PlantAsset({required this.id, required this.size, required this.stem});

  final String id;
  final Size size;

  /// 줄기가 흙에 닿는 자리.
  final Offset stem;

  String get path => 'assets/plants/$id.png';
}

class ShadowAsset {
  const ShadowAsset(this.id, this.size, this.anchor);

  final String id;
  final Size size;
  final Offset anchor;

  String get path => 'assets/shadows/$id.png';
}

/// 바닥 격자. 온실 그림의 바닥 네 꼭짓점에서 재서 만듭니다.
///
/// 마름모가 완전히 대칭이 아닐 수 있어 두 방향 벡터로 들고 있습니다.
/// 폭·높이 한 쌍으로 두면 살짝 기운 바닥에서 어긋납니다.
class GridSpec {
  const GridSpec({
    required this.size,
    required this.top,
    required this.u,
    required this.v,
    required this.tileW,
    required this.tileH,
    required this.sceneW,
    required this.sceneH,
    required this.unit,
  });

  final int size;

  /// 격자의 뒤쪽 꼭짓점.
  final Offset top;

  /// i 가 1 늘 때의 이동, j 가 1 늘 때의 이동.
  final Offset u;
  final Offset v;

  final double tileW;
  final double tileH;
  final double sceneW;
  final double sceneH;

  /// 조각과 무대의 축척 차이를 메우는 배율.
  ///
  /// 조각은 시트 아래 칸에 크게 그려져 있고 무대의 타일은 작습니다.
  /// 화분과 식물에 같은 값을 곱해야 둘의 비율이 유지됩니다.
  final double unit;
}

class Catalog {
  const Catalog(this.pots, this.plants, this.grid, this.stage, this.floor);

  final Map<String, PotAsset> pots;
  final Map<String, PlantAsset> plants;
  final GridSpec grid;

  /// 온실 그림. 유리·벽·소품이 들어 있습니다.
  final ui.Image stage;

  /// 그 위에 덮는 바닥. 우리 격자에 맞춰 다시 깐 타일입니다.
  ///
  /// 받은 그림의 칠해진 타일은 간격이 제각각이라 우리 격자와 겹치면 두
  /// 겹으로 보였습니다. 바닥 픽셀에만 씌우므로 작업대 다리는 그대로입니다.
  final ui.Image floor;

  /// 기준이 되는 흙 폭. 자리마다 식물 크기를 맞출 때 씁니다.
  /// 둥근 화분(자리가 하나인 것) 중 첫 번째를 기준으로 삼습니다.
  double get referenceSoilWidth {
    for (final p in pots.values) {
      if (p.slots.length == 1) return p.slots.first.width;
    }
    return pots.values.first.slots.first.width;
  }

  static double _d(Map m, String k) => (m[k] as num).toDouble();

  static Future<Catalog> load() async {
    final m = json.decode(await rootBundle.loadString('assets/catalog.json'))
        as Map<String, dynamic>;

    final pots = <String, PotAsset>{};
    for (final e in (m['pots'] as Map<String, dynamic>).entries) {
      final v = e.value as Map<String, dynamic>;
      final sh = v['shadow'] as Map<String, dynamic>;
      pots[e.key] = PotAsset(
        id: e.key,
        size: Size(_d(v, 'w'), _d(v, 'h')),
        foot: Offset(_d(v['foot'] as Map, 'x'), _d(v['foot'] as Map, 'y')),
        slots: [
          for (final s in v['slots'] as List)
            Slot(_d(s as Map, 'x'), _d(s, 'y'), _d(s, 'w')),
        ],
        span: [
          for (final s in (v['span'] as List? ??
              const [
                [0, 0]
              ]))
            ((s as List)[0] as int, s[1] as int),
        ],
        shadow: ShadowAsset(
          e.key,
          Size(_d(sh, 'w'), _d(sh, 'h')),
          Offset(_d(sh, 'anchorX'), _d(sh, 'anchorY')),
        ),
      );
    }

    final plants = <String, PlantAsset>{};
    for (final e in (m['plants'] as Map<String, dynamic>).entries) {
      final v = e.value as Map<String, dynamic>;
      plants[e.key] = PlantAsset(
        id: e.key,
        size: Size(_d(v, 'w'), _d(v, 'h')),
        stem: Offset(_d(v, 'stemX'), _d(v, 'stemY')),
      );
    }

    final g = m['grid'] as Map<String, dynamic>;

    Future<ui.Image> image(String path) async {
      final data = await rootBundle.load(path);
      final codec = await ui.instantiateImageCodec(data.buffer.asUint8List());
      return (await codec.getNextFrame()).image;
    }

    return Catalog(
      pots,
      plants,
      GridSpec(
        size: g['n'] as int,
        top: Offset(_d(g, 'topX'), _d(g, 'topY')),
        u: Offset(_d(g, 'uX'), _d(g, 'uY')),
        v: Offset(_d(g, 'vX'), _d(g, 'vY')),
        tileW: _d(g, 'tileW'),
        tileH: _d(g, 'tileH'),
        sceneW: _d(g, 'sceneW'),
        sceneH: _d(g, 'sceneH'),
        unit: _d(g, 'unitScale'),
      ),
      await image('assets/greenhouse/stage.png'),
      await image('assets/greenhouse/floor.png'),
    );
  }
}

const plantNames = {
  'monstera': '몬스테라',
  'strelitzia': '극락조',
  'bamboo': '행운목',
};

const potNames = {
  'pot_terracotta': '테라코타',
  'pot_white': '흰 도자기',
  'bed_wood': '나무 화단',
};
