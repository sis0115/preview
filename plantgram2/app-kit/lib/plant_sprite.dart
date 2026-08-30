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
    required this.footDrop,
  });

  final Size size;

  /// 상자 안에서 기준점(화분의 심는 자리 한가운데)이 있는 곳.
  final Offset anchor;
  final double scale;

  /// 심는 자리에서 화분 바닥까지. 그림자를 여기에 깝니다.
  final double footDrop;

  static SpriteLayout of(Catalog cat, String plantId, String potId,
      double userScale) {
    // 시트의 조각은 무대보다 크게 그려져 있습니다. 그 차이를 메운 뒤
    // 사용자가 키운 만큼을 곱합니다.
    final s = cat.grid.unit * userScale;
    final pot = cat.pots[potId]!;
    final plant = cat.plants[plantId]!;
    final pa = pot.anchor;
    final footDrop = (pot.bottom - pa.dy) * s;
    final refSoil = cat.referenceSoilWidth;

    var l = 0.0, r = 0.0, t = 0.0, b = 0.0;
    void extend(Offset origin, Size sz, Offset anchor, double dy) {
      final o = (origin - anchor) * s + Offset(0, dy);
      l = math.max(l, -o.dx);
      t = math.max(t, -o.dy);
      r = math.max(r, o.dx + sz.width * s);
      b = math.max(b, o.dy + sz.height * s);
    }

    // 화분 — 기준점이 원점에 오도록
    extend(Offset.zero, pot.size, pa, 0);
    // 그림자 — 화분 바닥에
    extend(Offset.zero, pot.shadow.size, pot.shadow.anchor, footDrop);
    // 식물 — 심는 자리마다 하나씩.
    // 밑동이 심는 자리에 오게 하려면 원점을 (자리 - 화분기준점) 으로 둡니다.
    // 여기에 밑동을 한 번 더 더하면 그만큼 아래로 밀립니다.
    for (final slot in pot.slots) {
      // 자리 폭에 맞춰 줄인 크기로 잽니다.
      final ps = s * pot.scaleFor(slot, refSoil);
      final o = (slot.offset - pa) * s - plant.stem * ps;
      l = math.max(l, -o.dx);
      t = math.max(t, -o.dy);
      r = math.max(r, o.dx + plant.size.width * ps);
      b = math.max(b, o.dy + plant.size.height * ps);
    }

    return SpriteLayout(
      size: Size(l + r, t + b),
      anchor: Offset(l, t),
      scale: s,
      footDrop: footDrop,
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
    this.selected = false,
  });

  final Catalog catalog;
  final String plantId;
  final String potId;
  final SpriteLayout layout;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final pot = catalog.pots[potId]!;
    final plant = catalog.plants[plantId]!;
    final pa = pot.anchor;
    final s = layout.scale;

    Widget layer(String path, Size sz, Offset anchor, Offset at, double dy) {
      final o = (at - anchor) * s + Offset(0, dy);
      return Positioned(
        left: layout.anchor.dx + o.dx,
        top: layout.anchor.dy + o.dy,
        width: sz.width * s,
        height: sz.height * s,
        child: Image.asset(path,
            fit: BoxFit.fill, filterQuality: FilterQuality.medium),
      );
    }

    final refSoil = catalog.referenceSoilWidth;

    /// 자리 하나에 식물 한 그루. 자리가 좁으면 그만큼 작게 심습니다.
    Widget plantAt(PlantAsset q, Slot slot, Offset pa, double base) {
      final ps = base * pot.scaleFor(slot, refSoil);
      final o = (slot.offset - pa) * base - q.stem * ps;
      return Positioned(
        left: layout.anchor.dx + o.dx,
        top: layout.anchor.dy + o.dy,
        width: q.size.width * ps,
        height: q.size.height * ps,
        child: Image.asset(q.path,
            fit: BoxFit.fill, filterQuality: FilterQuality.medium),
      );
    }

    // 뒤쪽 자리부터 심어야 앞 그루가 뒤 그루를 가립니다.
    final slots = [...pot.slots]..sort((a, b) => a.y.compareTo(b.y));

    return SizedBox.fromSize(
      size: layout.size,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          layer(pot.shadow.path, pot.shadow.size, pot.shadow.anchor,
              Offset.zero, layout.footDrop),
          layer(pot.path, pot.size, pa, Offset.zero, 0),
          for (final slot in slots) plantAt(plant, slot, pa, s),
          if (selected)
            Positioned.fill(
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    border: Border.all(color: const Color(0xFF5D9D6E), width: 2),
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
