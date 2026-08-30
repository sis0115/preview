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
    'id': id, 'plant': plantId, 'pot': potId,
    'i': cell.i, 'j': cell.j, 'scale': scale,
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

  /// 뒤에서 앞으로. 같은 칸이 없으므로 depth 만으로 정해집니다.
  List<PlacedPlant> get inDrawOrder =>
      [...plants]..sort((a, b) => a.cell.depth.compareTo(b.cell.depth));

  void select(int? id) {
    selectedId = id;
    notifyListeners();
  }

  bool add(String plantId, String potId, {Cell? at}) {
    final want = at ?? Cell(grid.size ~/ 2, grid.size ~/ 2);
    final free = occupied.contains(want) ? grid.nearestFree(want, occupied) : want;
    if (free == null) return false;
    plants.add(PlacedPlant(
        id: _nextId, plantId: plantId, potId: potId, cell: free));
    selectedId = _nextId++;
    notifyListeners();
    return true;
  }

  void moveTo(PlacedPlant p, Cell c) {
    final t = grid.clamp(c);
    if (t == p.cell || occupied.contains(t)) return;
    p.cell = t;
    notifyListeners();
  }

  void resize(PlacedPlant p, double factor) {
    p.scale = (p.scale * factor).clamp(.6, 1.7);
    notifyListeners();
  }

  void repot(PlacedPlant p, String potId) {
    p.potId = potId;
    notifyListeners();
  }

  void remove(PlacedPlant p) {
    plants.remove(p);
    if (selectedId == p.id) selectedId = null;
    notifyListeners();
  }

  // 저장은 배치 정보만 오갑니다. 이미지는 앱에 이미 들어 있습니다.
  String encode() =>
      json.encode({'version': 1, 'plants': [for (final p in plants) p.toJson()]});

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
