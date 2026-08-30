import 'dart:convert';
import 'dart:ui' as ui;

import 'package:flutter/services.dart';

/// 화분에 식물을 심는 자리 하나.
///
/// 긴 화단은 자리가 둘입니다. 등각이라 앞쪽 자리가 뒤쪽보다 아래에
/// 있으므로, 좌표를 각각 들고 있어야 두 그루가 나란히 앉습니다.
class Slot {
  const Slot(this.x, this.y);

  final double x;
  final double y;

  Offset get offset => Offset(x, y);
}

class PotAsset {
  const PotAsset({
    required this.id,
    required this.size,
    required this.slots,
    required this.foot,
    required this.shadow,
  });

  final String id;
  final Size size;
  final List<Slot> slots;

  /// 그림 안에서 화분이 바닥에 닿는 자리. 이 점을 칸 한가운데에 놓습니다.
  ///
  /// 흙이 아니라 닿는 자리입니다. 흙을 칸에 맞추면 흙은 화분 위쪽이라
  /// 키가 큰 화단일수록 다리가 제 칸보다 한참 앞으로 나갑니다.
  final Offset foot;

  final ShadowAsset shadow;

  String get path => 'assets/pots/$id.png';

  /// 식물 크기는 조각에 이미 들어 있습니다.
  ///
  /// 예전에는 자리 폭에 맞춰 코드가 줄였습니다. 이제는 등급별로 알맞은
  /// 크기의 식물을 따로 받으므로 코드가 크기를 건드리지 않습니다 —
  /// 등급이 안 맞으면 줄이는 게 아니라 놓을 수 없다고 알려 줍니다.
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
  const ShadowAsset(this.id, this.size, this.anchor, this.drop);

  final String id;
  final Size size;
  final Offset anchor;

  /// 닿는 자리에서 아래로 얼마나 내려 깔지.
  ///
  /// 다리 달린 선반·화단은 밑면 한가운데가 제 몸에 가려 그림자가 보이지
  /// 않습니다. 다리 끝 쪽으로 조금 내려야 앞으로 비칩니다.
  final double drop;

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
  const Catalog(this.pots, this.plants, this.grid, this.stage, this.names);

  final Map<String, PotAsset> pots;
  final Map<String, PlantAsset> plants;
  final GridSpec grid;

  /// 조각 이름. 시트를 갈아 끼워도 코드를 고치지 않도록 카탈로그에 둡니다.
  final Map<String, String> names;

  /// 온실 그림. 바닥·유리·벽·소품이 모두 들어 있습니다.
  ///
  /// 바닥만 우리 격자대로 다시 깔아 본 적이 있는데, 벽과 소품은 그림 것을
  /// 쓰고 바닥만 우리가 그리니 각이 서로 어긋나 뒤틀려 보였습니다.
  /// 그림은 그림대로 씁니다.
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
        foot: Offset(_d(v['foot'] as Map, 'x'), _d(v['foot'] as Map, 'y')),
        slots: [
          for (final s in v['slots'] as List)
            Slot(_d(s as Map, 'x'), _d(s, 'y')),
        ],
        shadow: ShadowAsset(
          e.key,
          Size(_d(sh, 'w'), _d(sh, 'h')),
          Offset(_d(sh, 'anchorX'), _d(sh, 'anchorY')),
          _d(sh, 'drop'),
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
      {
        for (final e in (m['names'] as Map<String, dynamic>).entries)
          e.key: e.value as String,
      },
    );
  }
}
