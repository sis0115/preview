import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'catalog.dart';

/// 그림자 · 화분 · 식물을 겹쳤을 때의 상자와 기준점.
///
/// 크기를 미리 계산해 둡니다. 크기 0짜리 상자에 겹쳐 놓으면 Flutter 가
/// 자식에게 무한 제약을 주면서 아무것도 그리지 않습니다.
@immutable
class SpriteLayout {
  const SpriteLayout({
    required this.size,
    required this.anchor,
    required this.scale,
  });

  final Size size;

  /// 상자 안에서 기준점(화분이 바닥에 닿는 자리)이 있는 곳.
  ///
  /// 이 점이 화분이 덮는 칸들의 한가운데에 놓입니다. 화단이면 두 칸의
  /// 한가운데, 곧 두 칸 사이 경계입니다.
  final Offset anchor;

  /// 시트에서 무대로 옮기는 배율.
  final double scale;

  static SpriteLayout of(
      Catalog cat, String plantId, String potId, double userScale) {
    // 시트의 조각은 무대보다 크게 그려져 있습니다. 그 차이를 메운 뒤
    // 사용자가 키운 만큼을 곱합니다.
    final s = cat.grid.unit * userScale;
    final pot = cat.pots[potId]!;
    final plant = cat.plants[plantId]!;
    final foot = pot.foot;
    final refSoil = cat.referenceSoilWidth;

    var l = 0.0, r = 0.0, t = 0.0, b = 0.0;
    void extend(Offset origin, Size sz, double k) {
      l = math.max(l, -origin.dx);
      t = math.max(t, -origin.dy);
      r = math.max(r, origin.dx + sz.width * k);
      b = math.max(b, origin.dy + sz.height * k);
    }

    // 화분 — 닿는 자리가 원점에 오도록
    extend(-foot * s, pot.size, s);
    // 그림자 — 닿는 자리에 그대로
    extend(-pot.shadow.anchor * s, pot.shadow.size, s);
    // 식물 — 심는 자리마다 하나씩.
    // 밑동이 심는 자리에 오게 하려면 원점을 (자리 - 닿는자리) 로 둡니다.
    // 여기에 밑동을 한 번 더 더하면 그만큼 아래로 밀립니다.
    for (final slot in pot.slots) {
      final ls = s * pot.scaleFor(slot, refSoil);
      extend((slot.offset - foot) * s - plant.stem * ls, plant.size, ls);
    }

    return SpriteLayout(
      size: Size(l + r, t + b),
      anchor: Offset(l, t),
      scale: s,
    );
  }
}

/// 화분 식물 한 그루. 긴 화단이면 같은 식물을 심는 자리 수만큼 심습니다.
class PlantSprite extends StatelessWidget {
  const PlantSprite({
    super.key,
    required this.catalog,
    required this.plantId,
    required this.potId,
    required this.layout,
  });

  final Catalog catalog;
  final String plantId;
  final String potId;
  final SpriteLayout layout;

  @override
  Widget build(BuildContext context) {
    final pot = catalog.pots[potId]!;
    final plant = catalog.plants[plantId]!;
    final foot = pot.foot;
    final ps = layout.scale;

    Widget at(String path, Size sz, Offset origin, double s) => Positioned(
          left: layout.anchor.dx + origin.dx,
          top: layout.anchor.dy + origin.dy,
          width: sz.width * s,
          height: sz.height * s,
          child: Image.asset(path,
              fit: BoxFit.fill, filterQuality: FilterQuality.medium),
        );

    final refSoil = catalog.referenceSoilWidth;

    Widget plantAt(Slot slot) {
      final ls = ps * pot.scaleFor(slot, refSoil);
      return at(plant.path, plant.size,
          (slot.offset - foot) * ps - plant.stem * ls, ls);
    }

    // 뒤쪽 자리부터 심어야 앞 그루가 뒤 그루를 가립니다.
    final slots = [...pot.slots]..sort((a, b) => a.y.compareTo(b.y));

    return SizedBox.fromSize(
      size: layout.size,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          at(pot.shadow.path, pot.shadow.size, -pot.shadow.anchor * ps, ps),
          at(pot.path, pot.size, -foot * ps, ps),
          for (final slot in slots) plantAt(slot),
        ],
      ),
    );
  }
}
