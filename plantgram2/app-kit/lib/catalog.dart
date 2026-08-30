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
    required this.bottom,
    required this.shadow,
  });

  final String id;
  final Size size;
  final List<Slot> slots;

  /// 그림 안에서 화분 바닥의 y. 그림자를 여기에 깝니다.
  final double bottom;
  final ShadowAsset shadow;

  String get path => 'assets/pots/$id.png';

  /// 칸 한가운데에 놓을 기준점. 심는 자리들의 한가운데입니다.
  Offset get anchor {
    var x = 0.0, y = 0.0;
    for (final s in slots) {
      x += s.x;
      y += s.y;
    }
    return Offset(x / slots.length, y / slots.length);
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
  const Catalog(this.pots, this.plants, this.grid, this.stage);

  final Map<String, PotAsset> pots;
  final Map<String, PlantAsset> plants;
  final GridSpec grid;
  final ui.Image stage;

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
        bottom: _d(v, 'bottom'),
        slots: [
          for (final s in v['slots'] as List)
            Slot(_d(s as Map, 'x'), _d(s, 'y'), _d(s, 'w')),
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
    final data = await rootBundle.load('assets/greenhouse/stage.png');
    final codec = await ui.instantiateImageCodec(data.buffer.asUint8List());

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
      (await codec.getNextFrame()).image,
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
