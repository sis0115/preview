import 'dart:convert';

import 'dart:ui' show Offset;

import 'package:flutter/foundation.dart';

import 'catalog.dart';
import 'iso.dart';

/// 온실에 놓인 그릇 하나와 그 안에 심긴 것들.
///
/// 자리를 화면 좌표가 아니라 칸으로 들고 있습니다. 그래야 확대·이동과
/// 무관하게 자리가 유지되고, 앞뒤 순서를 칸만으로 정할 수 있습니다.
///
/// 한 그릇에 심는 자리가 여럿일 수 있습니다 - 긴 화단은 둘, 둥근 화분은
/// 하나, 선반은 아직 없습니다. [slots] 는 그릇의 자리 수와 길이가 같고,
/// 비어 있으면 null 입니다.
class PlacedPlant {
  PlacedPlant({
    required this.id,
    required this.potId,
    required this.cell,
    required this.slots,
    this.rot = 0,
    this.scale = 1,
  });

  final int id;
  String potId;
  Cell cell;
  final List<String?> slots;

  /// 놓인 방향. 0 = 오른쪽 위로 뻗음, 1 = 왼쪽 위로 뻗음(좌우 뒤집기).
  int rot;
  double scale;

  /// 자리가 없으면 가구입니다. 식물을 담지 못합니다.
  bool get isFurniture => slots.isEmpty;
  bool get isEmpty => slots.every((s) => s == null);
  int get filled => slots.where((s) => s != null).length;

  /// 이름표에 쓸 대표 식물. 비어 있으면 그릇 이름을 씁니다.
  String? get anyPlant {
    for (final s in slots) {
      if (s != null) return s;
    }
    return null;
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'pot': potId,
        'i': cell.i,
        'j': cell.j,
        'slots': slots,
        'rot': rot,
        'scale': scale,
      };

  static PlacedPlant fromJson(Map<String, dynamic> m) => PlacedPlant(
        id: m['id'] as int,
        potId: m['pot'] as String,
        cell: Cell(m['i'] as int, m['j'] as int),
        slots: [
          for (final s in (m['slots'] as List? ?? const [])) s as String?,
        ],
        rot: (m['rot'] as int?) ?? 0,
        scale: (m['scale'] as num).toDouble(),
      );
}

class Garden extends ChangeNotifier {
  Garden(this.grid, this.pots);

  final IsoGrid grid;

  /// 그릇마다 자리가 몇 개인지 알아야 심을 수 있습니다.
  final Map<String, PotAsset> pots;
  final List<PlacedPlant> plants = [];
  int? selectedId;
  int _nextId = 1;

  PlacedPlant? get selected {
    for (final p in plants) {
      if (p.id == selectedId) return p;
    }
    return null;
  }

  /// 그 조각이 실제로 덮는 칸들.
  List<Cell> cellsOf(PlacedPlant p) =>
      IsoGrid.footprint(p.cell, pots[p.potId]!.cells, p.rot);

  /// 그 조각이 놓이는 점. 여러 칸에 걸치면 그 칸들의 한가운데입니다.
  Offset anchorOf(PlacedPlant p) =>
      grid.anchor(p.cell, pots[p.potId]!.cells, p.rot);

  Set<Cell> get occupied => {
        for (final p in plants) ...cellsOf(p),
      };

  PlacedPlant? at(Cell c) {
    for (final p in plants) {
      if (cellsOf(p).contains(c)) return p;
    }
    return null;
  }

  /// 덮는 칸이 **모두** 격자 안이고 비어 있어야 놓입니다.
  ///
  /// 맨 앞 칸만 보면 두 칸짜리 조각이 뒤 칸을 말없이 침범합니다.
  bool fits(Cell c, String potId, {int rot = 0, int? ignore}) {
    final want = IsoGrid.footprint(c, pots[potId]!.cells, rot);
    if (!want.every(grid.contains)) return false;
    for (final p in plants) {
      if (p.id == ignore) continue;
      final has = cellsOf(p);
      if (want.any(has.contains)) return false;
    }
    return true;
  }

  /// [from] 에서 가장 가까운, 그 조각이 들어갈 수 있는 칸.
  Cell? nearestFree(Cell from, String potId, {int rot = 0, int? ignore}) {
    Cell? best;
    var bestD = 1 << 30;
    for (final c in grid.cells) {
      if (!fits(c, potId, rot: rot, ignore: ignore)) continue;
      final d =
          (c.i - from.i) * (c.i - from.i) + (c.j - from.j) * (c.j - from.j);
      if (d < bestD) {
        bestD = d;
        best = c;
      }
    }
    return best;
  }

  /// 앞뒤 순서의 기준. 그 조각이 덮은 칸 중 **가장 앞** 칸의 화면 높이입니다.
  ///
  /// 화면에서 아래에 있는 것이 앞이라는 규칙은 언제나 맞습니다. 칸 합
  /// (i+j) 으로 정하면 두 축의 기울기가 다를 때 순서가 흔들립니다.
  double footY(PlacedPlant p) {
    var y = double.negativeInfinity;
    for (final c in cellsOf(p)) {
      final d = grid.center(c).dy;
      if (d > y) y = d;
    }
    return y;
  }

  /// 뒤에서 앞으로.
  List<PlacedPlant> get inDrawOrder =>
      [...plants]..sort((a, b) => footY(a).compareTo(footY(b)));

  void select(int? id) {
    selectedId = id;
    notifyListeners();
  }

  /// 그릇을 놓습니다. [plantId] 를 주면 첫 자리에 심습니다.
  bool add(String? plantId, String potId, {Cell? at, int rot = 0}) {
    final want = at ?? Cell(grid.size ~/ 2, grid.size ~/ 2);
    final cell = fits(want, potId, rot: rot)
        ? want
        : nearestFree(want, potId, rot: rot);
    if (cell == null) return false;
    final slots = pots[potId]!.slots;
    plants.add(PlacedPlant(
      id: _nextId,
      potId: potId,
      cell: cell,
      rot: rot,
      slots: [
        for (var k = 0; k < slots.length; k++)
          k == 0 && plantId != null && slots[k].takes(plantId)
              ? plantId
              : null,
      ],
    ));
    selectedId = _nextId++;
    notifyListeners();
    return true;
  }

  /// 자리 하나에 심거나 비웁니다.
  ///
  /// 등급이 맞지 않으면 크기를 조절하지 않고 거절합니다(RULES 8). 왜
  /// 안 되는지 부르는 쪽에서 알려 줄 수 있도록 이유를 돌려줍니다.
  String? plantInto(PlacedPlant p, int slot, String? plantId) {
    final want = pots[p.potId]!.slots[slot];
    if (plantId != null && !want.takes(plantId)) {
      return '이 자리는 ${want.grades.join(" · ")} 자리입니다';
    }
    p.slots[slot] = plantId;
    notifyListeners();
    return null;
  }

  void moveTo(PlacedPlant p, Cell c) {
    if (c == p.cell || !fits(c, p.potId, rot: p.rot, ignore: p.id)) return;
    p.cell = c;
    notifyListeners();
  }

  /// 그릇을 바꿉니다. 새 그릇이 더 넓어 옆 칸을 침범하면 바꾸지 않습니다.
  bool repot(PlacedPlant p, String potId) {
    if (!fits(p.cell, potId, rot: p.rot, ignore: p.id)) return false;
    p.potId = potId;
    notifyListeners();
    return true;
  }

  /// 90도 돌립니다. 돌린 자리가 옆 칸을 침범하면 돌리지 않습니다.
  bool turn(PlacedPlant p) {
    final next = 1 - p.rot;
    if (!fits(p.cell, p.potId, rot: next, ignore: p.id)) return false;
    p.rot = next;
    notifyListeners();
    return true;
  }

  void resize(PlacedPlant p, double factor) {
    p.scale = (p.scale * factor).clamp(.6, 1.7);
    notifyListeners();
  }

  void remove(PlacedPlant p) {
    plants.remove(p);
    if (selectedId == p.id) selectedId = null;
    notifyListeners();
  }

  // 저장은 배치 정보만 오갑니다. 이미지는 앱에 이미 들어 있습니다.
  String encode() => json.encode({
        'version': 1,
        'plants': [for (final p in plants) p.toJson()],
      });

  void decode(String src) {
    final m = json.decode(src) as Map<String, dynamic>;
    plants
      ..clear()
      ..addAll(
        (m['plants'] as List).map(
          (e) => PlacedPlant.fromJson(e as Map<String, dynamic>),
        ),
      );
    _nextId = plants.fold(0, (a, p) => a > p.id ? a : p.id) + 1;
    selectedId = null;
    notifyListeners();
  }
}
