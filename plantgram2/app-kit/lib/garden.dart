import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'catalog.dart';
import 'iso.dart';

/// 온실에 놓인 화분 식물 하나.
///
/// 자리를 화면 좌표가 아니라 칸으로 들고 있습니다. 그래야 확대·이동과
/// 무관하게 자리가 유지되고, 앞뒤 순서를 칸만으로 정할 수 있습니다.
///
/// [cell] 은 기준 칸 하나입니다. 실제로 덮는 칸은 화분에 따라 늘어납니다 —
/// 긴 화단은 두 칸입니다. [Garden.cellsOf] 로 물어봅니다.
class PlacedPlant {
  PlacedPlant({
    required this.id,
    required this.plantId,
    required this.potId,
    required this.cell,
    this.scale = 1,
  });

  final int id;
  String plantId;
  String potId;
  Cell cell;
  double scale;

  Map<String, dynamic> toJson() => {
        'id': id,
        'plant': plantId,
        'pot': potId,
        'i': cell.i,
        'j': cell.j,
        'scale': scale,
      };

  static PlacedPlant fromJson(Map<String, dynamic> m) => PlacedPlant(
        id: m['id'] as int,
        plantId: m['plant'] as String,
        potId: m['pot'] as String,
        cell: Cell(m['i'] as int, m['j'] as int),
        scale: (m['scale'] as num).toDouble(),
      );
}

class Garden extends ChangeNotifier {
  Garden(this.grid, this.catalog);

  final IsoGrid grid;
  final Catalog catalog;
  final List<PlacedPlant> plants = [];
  int? selectedId;
  int _nextId = 1;

  PlacedPlant? get selected {
    for (final p in plants) {
      if (p.id == selectedId) return p;
    }
    return null;
  }

  /// 기준 칸이 [base] 일 때 [potId] 화분이 덮는 칸들.
  List<Cell> cellsFor(Cell base, String potId) => [
        for (final (di, dj) in catalog.pots[potId]!.span)
          Cell(base.i + di, base.j + dj),
      ];

  List<Cell> cellsOf(PlacedPlant p) => cellsFor(p.cell, p.potId);

  Set<Cell> get occupied => {for (final p in plants) ...cellsOf(p)};

  /// [ignore] 번 식물을 뺀 나머지가 차지한 칸.
  Set<Cell> _takenExcept(int? ignore) => {
        for (final p in plants)
          if (p.id != ignore) ...cellsOf(p)
      };

  /// 기준 칸 [base] 에 [potId] 화분을 놓을 수 있는지.
  ///
  /// 덮는 칸이 전부 격자 안에 있고 비어 있어야 합니다. 화단은 두 칸이므로
  /// 가장자리 한 칸만 남았을 때는 놓을 수 없습니다.
  bool fits(Cell base, String potId, {int? ignore}) {
    final taken = _takenExcept(ignore);
    for (final c in cellsFor(base, potId)) {
      if (!grid.contains(c) || taken.contains(c)) return false;
    }
    return true;
  }

  /// [from] 에서 가장 가까우면서 화분이 들어가는 기준 칸.
  Cell? nearestFit(Cell from, String potId, {int? ignore}) {
    Cell? best;
    var bestD = 1 << 30;
    for (final c in grid.cells) {
      if (!fits(c, potId, ignore: ignore)) continue;
      final d =
          (c.i - from.i) * (c.i - from.i) + (c.j - from.j) * (c.j - from.j);
      if (d < bestD) {
        bestD = d;
        best = c;
      }
    }
    return best;
  }

  /// 화분이 바닥에 닿는 자리의 화면 높이. 앞뒤 순서의 기준입니다.
  ///
  /// 칸 합(i+j)으로 정하면 두 칸짜리 화단과 한 칸짜리 화분이 자주 같은
  /// 값이 되어 순서가 흔들립니다. 화면에서 아래에 있는 것이 앞이라는
  /// 규칙은 칸 수와 무관하게 언제나 맞습니다.
  double footY(PlacedPlant p) {
    final cs = cellsOf(p);
    var y = 0.0;
    for (final c in cs) {
      y += grid.center(c).dy;
    }
    return y / cs.length;
  }

  /// 뒤에서 앞으로.
  List<PlacedPlant> get inDrawOrder =>
      [...plants]..sort((a, b) => footY(a).compareTo(footY(b)));

  void select(int? id) {
    selectedId = id;
    notifyListeners();
  }

  bool add(String plantId, String potId, {Cell? at}) {
    final want = at ?? Cell(grid.size ~/ 2, grid.size ~/ 2);
    final base = fits(want, potId) ? want : nearestFit(want, potId);
    if (base == null) return false;
    plants.add(
        PlacedPlant(id: _nextId, plantId: plantId, potId: potId, cell: base));
    selectedId = _nextId++;
    notifyListeners();
    return true;
  }

  void moveTo(PlacedPlant p, Cell c) {
    if (c == p.cell || !fits(c, p.potId, ignore: p.id)) return;
    p.cell = c;
    notifyListeners();
  }

  /// 화분을 바꿉니다. 칸 수가 늘어 자리가 모자라면 가까운 빈 자리로
  /// 옮겨서라도 심고, 그마저 없으면 그대로 두고 false 를 돌려줍니다.
  bool repot(PlacedPlant p, String potId) {
    if (p.potId == potId) return true;
    final base = fits(p.cell, potId, ignore: p.id)
        ? p.cell
        : nearestFit(p.cell, potId, ignore: p.id);
    if (base == null) return false;
    p.potId = potId;
    p.cell = base;
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
        'plants': [for (final p in plants) p.toJson()]
      });

  void decode(String src) {
    final m = json.decode(src) as Map<String, dynamic>;
    plants
      ..clear()
      ..addAll((m['plants'] as List)
          .map((e) => PlacedPlant.fromJson(e as Map<String, dynamic>)));
    _nextId = plants.fold(0, (a, p) => a > p.id ? a : p.id) + 1;
    selectedId = null;
    notifyListeners();
  }
}
