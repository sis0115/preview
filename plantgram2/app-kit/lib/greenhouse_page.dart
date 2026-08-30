import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';

import 'catalog.dart';
import 'garden.dart';
import 'iso.dart';
import 'plant_sprite.dart';

const _ink = Color(0xFF2E4034);
const _mut = Color(0xFF7B8A81);
const _leaf = Color(0xFF5D8B6A);
const _card = Color(0xFFFFFFFF);

class GreenhousePage extends StatefulWidget {
  const GreenhousePage({super.key, required this.catalog});

  final Catalog catalog;

  @override
  State<GreenhousePage> createState() => _GreenhousePageState();
}

class _GreenhousePageState extends State<GreenhousePage> {
  late final IsoGrid grid = IsoGrid(widget.catalog.grid);
  late final Garden garden = Garden(grid);
  final view = TransformationController();

  bool showGrid = false;
  String? saved;
  double _base = 1;
  bool _fitted = false;

  @override
  void initState() {
    super.initState();
    garden
      ..add('monstera', 'pot_terracotta', at: const Cell(1, 1))
      ..add('strelitzia', 'pot_white', at: const Cell(3, 1))
      ..add('bamboo', 'bed_wood', at: const Cell(2, 3))
      ..select(null);
  }

  @override
  void dispose() {
    view.dispose();
    super.dispose();
  }

  void _fitOnce(Size box) {
    if (_fitted || box.isEmpty) return;
    _fitted = true;
    final g = widget.catalog.grid;
    final s = math.min(box.width / g.sceneW, box.height / g.sceneH);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      view.value = Matrix4.identity()
        ..translateByDouble((box.width - g.sceneW * s) / 2,
            (box.height - g.sceneH * s) / 2, 0, 1)
        ..scaleByDouble(s, s, 1, 1);
      _base = s;
    });
  }

  void _zoom(double by) {
    final cur = view.value.getMaxScaleOnAxis();
    final next = (cur * by).clamp(_base * .8, _base * 3);
    view.value = view.value.clone()
      ..scaleByDouble(next / cur, next / cur, 1, 1);
  }

  double get _sceneScale => 1 / view.value.getMaxScaleOnAxis();

  @override
  Widget build(BuildContext context) {
    final g = widget.catalog.grid;
    return Scaffold(
      backgroundColor: const Color(0xFFF4F4EE),
      body: SafeArea(
        child: Column(
          children: [
            _header(),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Center(
                  child: AspectRatio(
                    aspectRatio: g.sceneW / g.sceneH,
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(24),
                      child: _scene(g),
                    ),
                  ),
                ),
              ),
            ),
            _panel(),
            _tray(),
          ],
        ),
      ),
    );
  }

  Widget _header() => Padding(
    padding: const EdgeInsets.fromLTRB(18, 12, 18, 8),
    child: Row(
      children: [
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('우리집 온실',
                  style: TextStyle(
                      fontSize: 23, fontWeight: FontWeight.w800, color: _ink)),
              SizedBox(height: 2),
              Text('식물을 눌러 고르고, 끌어서 칸에 옮기세요',
                  style: TextStyle(color: _mut, fontSize: 13)),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
          decoration: BoxDecoration(
              color: _card, borderRadius: BorderRadius.circular(18)),
          child: const Text('Lv. 8  ·  6,394 GP',
              style: TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 12.5,
                  color: Color(0xFF557C61))),
        ),
      ],
    ),
  );

  /// 온실 그림과 식물이 한 좌표계 안에 있습니다. 배경만 확대하면 식물이
  /// 따라오지 않으므로, 둘을 한 상자에 넣고 그 상자를 통째로 확대합니다.
  Widget _scene(GridSpec g) => LayoutBuilder(builder: (context, box) {
    _fitOnce(box.biggest);
    return InteractiveViewer(
      transformationController: view,
      // 자식을 뷰포트 크기로 누르지 않습니다. 눌리면 그림의 픽셀 좌표계가
      // 찌그러져 식물이 엉뚱한 데로 갑니다.
      constrained: false,
      minScale: .3,
      maxScale: 3,
      boundaryMargin: const EdgeInsets.all(400),
      child: SizedBox(
        width: g.sceneW,
        height: g.sceneH,
        child: AnimatedBuilder(
          animation: garden,
          builder: (context, _) => Stack(
            clipBehavior: Clip.none,
            children: [
              Positioned.fill(
                child: CustomPaint(
                  painter: _StagePainter(widget.catalog.stage,
                      showGrid ? grid : null, garden.occupied),
                ),
              ),
              Positioned.fill(
                child: GestureDetector(
                  behavior: HitTestBehavior.translucent,
                  onTapDown: (d) {
                    final c = grid.cellAt(d.localPosition);
                    garden.select(null);
                    if (grid.contains(c)) _tapEmpty(c);
                  },
                ),
              ),
              // 뒤에서 앞으로 — 칸 좌표 (i+j) 오름차순
              for (final p in garden.inDrawOrder) _sprite(p),
              Positioned(right: 12, top: 12, child: _zoomBar()),
            ],
          ),
        ),
      ),
    );
  });

  Widget _sprite(PlacedPlant p) {
    final at = grid.center(p.cell);
    final layout =
        SpriteLayout.of(widget.catalog, p.plantId, p.potId, p.scale);
    return Positioned(
      left: at.dx - layout.anchor.dx,
      top: at.dy - layout.anchor.dy,
      width: layout.size.width,
      height: layout.size.height,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => garden.select(p.id),
        onScaleStart: (_) => garden.select(p.id),
        onScaleUpdate: (d) {
          if (d.pointerCount == 1) {
            // 확대 중이면 손가락 이동을 배율로 나눠 그림 좌표로 되돌립니다.
            garden.moveTo(
                p,
                grid.cellAt(
                    grid.center(p.cell) + d.focalPointDelta * _sceneScale));
          } else if (d.scale != 1) {
            garden.resize(p, d.scale);
          }
        },
        child: PlantSprite(
          catalog: widget.catalog,
          plantId: p.plantId,
          potId: p.potId,
          layout: layout,
          selected: garden.selectedId == p.id,
        ),
      ),
    );
  }

  void _tapEmpty(Cell c) {
    if (garden.occupied.contains(c)) return;
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: const Color(0xFFF4F4EE),
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${c.i + 1}번째 줄 ${c.j + 1}번째 칸에 심기',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w800, color: _ink)),
              const SizedBox(height: 12),
              Row(
                children: [
                  for (final k in widget.catalog.plants.keys)
                    Expanded(
                      child: _pick(
                        label: plantNames[k] ?? k,
                        asset: widget.catalog.plants[k]!.path,
                        onTap: () {
                          garden.add(k, 'pot_terracotta', at: c);
                          Navigator.pop(context);
                        },
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _pick({
    required String label,
    required String asset,
    required VoidCallback onTap,
    bool active = false,
  }) =>
      GestureDetector(
        onTap: onTap,
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 4),
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: active ? const Color(0xFFE4F0E5) : _card,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
                color: active ? _leaf : const Color(0xFFE2E2DD),
                width: active ? 2 : 1),
          ),
          child: Column(
            children: [
              SizedBox(height: 62, child: Image.asset(asset)),
              Text(label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontSize: 11.5, fontWeight: FontWeight.w700)),
            ],
          ),
        ),
      );

  Widget _zoomBar() => Container(
    decoration: BoxDecoration(
        color: _card.withValues(alpha: .92),
        borderRadius: BorderRadius.circular(18)),
    child: Column(
      children: [
        _icon(Icons.add, () => _zoom(1.2)),
        const Divider(height: 1),
        _icon(Icons.remove, () => _zoom(1 / 1.2)),
        const Divider(height: 1),
        _icon(Icons.fit_screen, () => setState(() => _fitted = false)),
      ],
    ),
  );

  Widget _icon(IconData i, VoidCallback f) => IconButton(
      onPressed: f,
      icon: Icon(i, size: 19),
      color: _ink,
      visualDensity: VisualDensity.compact);

  /// 고른 식물에 따라 바뀌는 아래 판.
  Widget _panel() => AnimatedBuilder(
    animation: garden,
    builder: (context, _) {
      final p = garden.selected;
      return Container(
        height: 72,
        width: double.infinity,
        padding: const EdgeInsets.fromLTRB(14, 8, 14, 8),
        child: p == null
            ? const Center(
                child: Text('빈 칸을 누르면 심고, 식물을 누르면 고릅니다',
                    style: TextStyle(color: _mut, fontSize: 13)))
            : Row(
                children: [
                  Text(plantNames[p.plantId] ?? p.plantId,
                      style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w800, color: _ink)),
                  const SizedBox(width: 8),
                  Text(potNames[p.potId] ?? p.potId,
                      style: const TextStyle(color: _mut, fontSize: 12.5)),
                  const Spacer(),
                  for (final k in widget.catalog.pots.keys)
                    Padding(
                      padding: const EdgeInsets.only(left: 6),
                      child: GestureDetector(
                        onTap: () => garden.repot(p, k),
                        child: Container(
                          width: 46,
                          height: 46,
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: _card,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                                color: p.potId == k
                                    ? _leaf
                                    : const Color(0xFFE2E2DD),
                                width: p.potId == k ? 2 : 1),
                          ),
                          child: Image.asset(widget.catalog.pots[k]!.path),
                        ),
                      ),
                    ),
                  const SizedBox(width: 6),
                  IconButton(
                      onPressed: () => garden.remove(p),
                      icon: const Icon(Icons.delete_outline, size: 20),
                      color: _mut),
                ],
              ),
      );
    },
  );

  Widget _tray() => Container(
    padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
    child: Row(
      children: [
        _flat(showGrid ? '격자 끄기' : '격자 보기',
            () => setState(() => showGrid = !showGrid)),
        const SizedBox(width: 8),
        _flat('저장', () {
          saved = garden.encode();
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text('온실을 저장했습니다'),
              duration: Duration(seconds: 1)));
        }),
        const SizedBox(width: 8),
        _flat('되돌리기', () {
          if (saved != null) garden.decode(saved!);
        }),
      ],
    ),
  );

  Widget _flat(String label, VoidCallback onTap) => Expanded(
    child: Material(
      color: _card,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Container(
          height: 44,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFE2E2DD)),
          ),
          child: Text(label,
              style: const TextStyle(
                  fontSize: 13.5, fontWeight: FontWeight.w700, color: _ink)),
        ),
      ),
    ),
  );
}

/// 온실 그림과, 켜면 격자를 그립니다.
class _StagePainter extends CustomPainter {
  _StagePainter(this.stage, this.grid, this.taken);

  final ui.Image stage;
  final IsoGrid? grid;
  final Set<Cell> taken;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawImageRect(
      stage,
      Rect.fromLTWH(0, 0, stage.width.toDouble(), stage.height.toDouble()),
      Offset.zero & size,
      Paint()..filterQuality = FilterQuality.medium,
    );
    final g = grid;
    if (g == null) return;
    final line = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.6
      ..color = const Color(0x88FF7A2F);
    final free = Paint()..color = const Color(0x1FFF7A2F);
    for (final c in g.cells) {
      final path = g.diamond(c);
      if (!taken.contains(c)) canvas.drawPath(path, free);
      canvas.drawPath(path, line);
    }
  }

  @override
  bool shouldRepaint(_StagePainter old) =>
      old.grid != grid || old.taken.length != taken.length;
}
