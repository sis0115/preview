import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'iso.dart';

/// 온실에 놓인 화분 식물 하나.
///
/// 자리를 화면 좌표가 아니라 칸으로 들고 있습니다. 그래야 확대·이동과
/// 무관하게 자리가 유지되고, 앞뒤 순서를 칸만으로 정할 수 있습니다.
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
  Garden(this.grid);

  final IsoGrid grid;
  final List<PlacedPlant> plants = [];
  int? selectedId;
  int _nextId = 1;

  PlacedPlant? get selected {
    for (final p in plants) {
      if (p.id == selectedId) return p;
    }
    return null;
  }

  Set<Cell> get occupied => {for (final p in plants) p.cell};

  PlacedPlant? at(Cell c) {
    for (final p in plants) {
      if (p.cell == c) return p;
    }
    return null;
  }

  bool fits(Cell c, {int? ignore}) {
    if (!grid.contains(c)) return false;
    for (final p in plants) {
      if (p.id != ignore && p.cell == c) return false;
    }
    return true;
  }

  /// [from] 에서 가장 가까운 빈 칸.
  Cell? nearestFree(Cell from, {int? ignore}) {
    Cell? best;
    var bestD = 1 << 30;
    for (final c in grid.cells) {
      if (!fits(c, ignore: ignore)) continue;
      final d =
          (c.i - from.i) * (c.i - from.i) + (c.j - from.j) * (c.j - from.j);
      if (d < bestD) {
        bestD = d;
        best = c;
      }
    }
    return best;
  }

  /// 화분이 놓인 자리의 화면 높이. 앞뒤 순서의 기준입니다.
  ///
  /// 화면에서 아래에 있는 것이 앞이라는 규칙은 언제나 맞습니다. 칸 합
  /// (i+j) 으로 정하면 두 축의 기울기가 다를 때 순서가 흔들립니다.
  double footY(PlacedPlant p) => grid.center(p.cell).dy;

  /// 뒤에서 앞으로.
  List<PlacedPlant> get inDrawOrder =>
      [...plants]..sort((a, b) => footY(a).compareTo(footY(b)));

  void select(int? id) {
    selectedId = id;
    notifyListeners();
  }

  bool add(String plantId, String potId, {Cell? at}) {
    final want = at ?? Cell(grid.size ~/ 2, grid.size ~/ 2);
    final cell = fits(want) ? want : nearestFree(want);
    if (cell == null) return false;
    plants.add(
      PlacedPlant(id: _nextId, plantId: plantId, potId: potId, cell: cell),
    );
    selectedId = _nextId++;
    notifyListeners();
    return true;
  }

  void moveTo(PlacedPlant p, Cell c) {
    if (c == p.cell || !fits(c, ignore: p.id)) return;
    p.cell = c;
    notifyListeners();
  }

  void repot(PlacedPlant p, String potId) {
    p.potId = potId;
    notifyListeners();
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
