import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';
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

  /// 바닥 격자는 늘 보입니다. 이 값은 진하게 볼지 여부입니다.
  bool strongGrid = false;
  String? saved;
  double _base = 1;
  bool _fitted = false;

  /// 끌고 있는 동안: 손가락을 따라가는 기준점과, 놓이려는 칸.
  Offset? _dragAt;
  Cell? _dropAt;
  bool _dropOk = true;

  @override
  void initState() {
    super.initState();
    garden
      ..add('xlarge', 'pot_xlarge', at: const Cell(0, 2))
      ..add('large', 'pot_large', at: const Cell(1, 4))
      ..add('medium', 'pot_medium', at: const Cell(3, 4))
      ..add('small', 'bed_long', at: const Cell(4, 2))
      ..add('sprout', 'pot_sprout', at: const Cell(2, 2))
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
                          fontSize: 23,
                          fontWeight: FontWeight.w800,
                          color: _ink)),
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
                      painter: _StagePainter(
                        stage: widget.catalog.stage,
                        grid: grid,
                        taken: garden.occupied,
                        strong: strongGrid,
                        mark: _markedCell(),
                        markOk: _dropOk,
                      ),
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
                  // 뒤에서 앞으로 — 화면에서 위에 있는 것부터
                  for (final p in garden.inDrawOrder) _sprite(p),
                  Positioned(right: 12, top: 12, child: _zoomBar()),
                ],
              ),
            ),
          ),
        );
      });

  /// 지금 표시할 칸. 끌고 있으면 놓이려는 자리, 아니면 고른 식물의 자리.
  Cell? _markedCell() => _dropAt ?? garden.selected?.cell;

  Widget _sprite(PlacedPlant p) {
    final at = grid.center(p.cell);
    final layout = SpriteLayout.of(widget.catalog, p.plantId, p.potId, p.scale);
    final pot = widget.catalog.pots[p.potId]!;
    final ps = layout.scale;
    // 손이 닿는 곳은 화분까지입니다. 잎은 옆 칸 위까지 뻗으므로, 잎이
    // 덮은 자리를 눌러도 그 밑의 화분이 잡혀야 합니다.
    final grip = Rect.fromLTWH(
      layout.anchor.dx - pot.foot.dx * ps,
      layout.anchor.dy - pot.foot.dy * ps,
      pot.size.width * ps,
      pot.size.height * ps,
    );
    return Positioned(
      left: at.dx - layout.anchor.dx,
      top: at.dy - layout.anchor.dy,
      width: layout.size.width,
      height: layout.size.height,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          IgnorePointer(
            child: PlantSprite(
              catalog: widget.catalog,
              plantId: p.plantId,
              potId: p.potId,
              layout: layout,
            ),
          ),
          Positioned.fromRect(
            rect: grip,
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: () => garden.select(p.id),
              onScaleStart: (_) {
                garden.select(p.id);
                setState(() {
                  _dragAt = grid.center(p.cell);
                  _dropAt = p.cell;
                  _dropOk = true;
                });
              },
              onScaleUpdate: (d) {
                if (d.pointerCount == 1) {
                  // 손가락 이동을 확대율로 나눠 그림 좌표로 되돌립니다. 칸이 아니라
                  // 기준점을 들고 다녀야 반 칸 미만의 움직임이 버려지지 않습니다.
                  final now = (_dragAt ?? grid.center(p.cell)) +
                      d.focalPointDelta * _sceneScale;
                  final c = grid.cellAt(now);
                  final ok = garden.fits(c, ignore: p.id);
                  setState(() {
                    _dragAt = now;
                    _dropAt = c;
                    _dropOk = ok;
                  });
                  if (ok) garden.moveTo(p, c);
                } else if (d.scale != 1) {
                  garden.resize(p, d.scale);
                }
              },
              onScaleEnd: (_) => setState(() {
                _dragAt = null;
                _dropAt = null;
                _dropOk = true;
              }),
            ),
          ),
        ],
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
                        label: widget.catalog.names[k] ?? k,
                        asset: widget.catalog.plants[k]!.path,
                        onTap: () {
                          garden.add(k, widget.catalog.plants[k]!.pot, at: c);
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
                      Text(widget.catalog.names[p.plantId] ?? p.plantId,
                          style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: _ink)),
                      const SizedBox(width: 8),
                      Text(widget.catalog.names[p.potId] ?? p.potId,
                          style: const TextStyle(color: _mut, fontSize: 12.5)),
                      const Spacer(),
                      // 가구(선반)는 식물을 담지 못하므로 고를 수 없습니다.
                      for (final k in widget.catalog.pots.keys
                          .where((k) => !widget.catalog.pots[k]!.isFurniture))
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
            _flat(strongGrid ? '칸선 끄기' : '칸선 보기',
                () => setState(() => strongGrid = !strongGrid)),
            const SizedBox(width: 8),
            _flat('저장', () {
              saved = garden.encode();
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                  content: Text('온실을 저장했습니다'), duration: Duration(seconds: 1)));
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
                      fontSize: 13.5,
                      fontWeight: FontWeight.w700,
                      color: _ink)),
            ),
          ),
        ),
      );
}

/// 온실 그림을 그리고, 그 위에 지금 노리는 칸을 표시합니다.
///
/// 바닥은 그림에 있는 것을 그대로 씁니다. 우리 격자대로 다시 깔아 본 적이
/// 있는데, 벽과 소품은 그림 것을 쓰고 바닥만 우리가 그리니 각이 서로
/// 어긋나 뒤틀려 보였습니다.
class _StagePainter extends CustomPainter {
  _StagePainter({
    required this.stage,
    required this.grid,
    required this.taken,
    required this.strong,
    required this.mark,
    required this.markOk,
  });

  final ui.Image stage;
  final IsoGrid grid;
  final Set<Cell> taken;

  /// 칸선을 또렷하게 볼지. 자리를 맞출 때 켭니다.
  final bool strong;

  /// 지금 노리는 칸.
  final Cell? mark;

  /// 그 자리에 놓을 수 있는지. 안 되면 붉게 표시합니다.
  final bool markOk;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawImageRect(
      stage,
      Rect.fromLTWH(0, 0, stage.width.toDouble(), stage.height.toDouble()),
      Offset.zero & size,
      Paint()..filterQuality = FilterQuality.medium,
    );

    if (strong) {
      final line = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4
        ..color = const Color(0xFF566052).withValues(alpha: .45);
      final free = Paint()
        ..color = const Color(0xFF566052).withValues(alpha: .07);
      for (final c in grid.cells) {
        final path = grid.diamond(c);
        if (!taken.contains(c)) canvas.drawPath(path, free);
        canvas.drawPath(path, line);
      }
    }

    final m = mark;
    if (m == null) return;
    final path = grid.diamond(m);
    final tint = markOk ? const Color(0xFF4E8C5E) : const Color(0xFFB4503F);
    canvas.drawPath(path, Paint()..color = tint.withValues(alpha: .24));
    canvas.drawPath(
      path,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.4
        ..color = tint.withValues(alpha: .85),
    );
  }

  @override
  bool shouldRepaint(_StagePainter o) =>
      o.strong != strong ||
      o.markOk != markOk ||
      o.mark != mark ||
      !setEquals(o.taken, taken);
}
