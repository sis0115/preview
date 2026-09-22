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
  late final Garden garden = Garden(grid, widget.catalog.pots);
  final view = TransformationController();

  /// 바닥 격자는 늘 보입니다. 이 값은 진하게 볼지 여부입니다.
  bool strongGrid = false;
  String? saved;
  double _base = 1;
  bool _fitted = false;

  /// 끌고 있는 동안: 손가락을 따라가는 기준점과, 놓이려는 칸.
  Offset? _dragAt;
  Cell? _dropAt;
  String? _dropPot;
  int? _dropRot;
  bool _dropOk = true;

  @override
  void initState() {
    super.initState();
    // 두 칸짜리끼리 겹치지 않는 자리로. 겹치면 add 가 가까운 빈 칸을
    // 찾아 옮기므로 조용히 어긋납니다.
    // 두 칸짜리는 누른 칸에서 뒤로 뻗습니다. 오른쪽 위로면 j 가, 왼쪽
    // 위로면 i 가 하나 줄어드는 칸을 함께 먹으므로, 가장자리에서는 방향에
    // 따라 놓을 수 없는 자리가 생깁니다.
    garden
      ..add('small', 'shelf_two', at: const Cell(1, 1))
      ..add('small', 'bench', at: const Cell(4, 2), rot: 1)
      ..add('small', 'bed_long', at: const Cell(2, 4))
      ..add('xlarge', 'pot_xlarge', at: const Cell(4, 4))
      ..add('sprout', 'pot_sprout', at: const Cell(2, 1))
      ..select(null);
    // 자리가 둘인 그릇은 첫 자리만 채우면 반쪽으로 보입니다.
    for (final c in [const Cell(1, 1), const Cell(4, 2), const Cell(2, 4)]) {
      final p = garden.at(c);
      if (p != null && p.slots.length > 1) garden.plantInto(p, 1, 'small');
    }

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
                        mark: _markedCells(),
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

  /// 지금 표시할 칸들. 끌고 있으면 놓이려는 자리, 아니면 고른 것의 자리.
  ///
  /// 두 칸짜리는 두 칸 모두 표시해야 합니다. 맨 앞 칸만 칠하면 뒤 칸이
  /// 비어 보이는데 실제로는 못 씁니다.
  List<Cell> _markedCells() {
    final c = _dropAt ?? garden.selected?.cell;
    if (c == null) return const [];
    final pot = _dropPot ?? garden.selected?.potId;
    final rot = _dropRot ?? garden.selected?.rot ?? 0;
    return IsoGrid.footprint(
        c, widget.catalog.pots[pot]?.cells ?? const [1, 1], rot);
  }

  Widget _sprite(PlacedPlant p) {
    final at = garden.anchorOf(p);
    final layout =
        SpriteLayout.of(widget.catalog, p.slots, p.potId, p.scale);
    final pot = widget.catalog.pots[p.potId]!;
    final ps = layout.scale;
    // 돌린 조각은 상자를 통째로 좌우 뒤집습니다. 그러면 상자 안에서
    // 기준점의 가로 위치도 반대편으로 갑니다.
    final flip = p.rot == 1;
    final ax = flip ? layout.size.width - layout.anchor.dx : layout.anchor.dx;
    // 손이 닿는 곳은 화분까지입니다. 잎은 옆 칸 위까지 뻗으므로, 잎이
    // 덮은 자리를 눌러도 그 밑의 화분이 잡혀야 합니다.
    var grip = Rect.fromLTWH(
      layout.anchor.dx - pot.foot.dx * ps,
      layout.anchor.dy - pot.foot.dy * ps,
      pot.size.width * ps,
      pot.size.height * ps,
    );
    if (flip) {
      grip = Rect.fromLTWH(layout.size.width - grip.right, grip.top,
          grip.width, grip.height);
    }
    return Positioned(
      left: at.dx - ax,
      top: at.dy - layout.anchor.dy,
      width: layout.size.width,
      height: layout.size.height,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          IgnorePointer(
            child: flip
                ? Transform(
                    alignment: Alignment.center,
                    transform: Matrix4.identity()..scaleByDouble(-1, 1, 1, 1),
                    child: PlantSprite(
                      catalog: widget.catalog,
                      slots: p.slots,
                      potId: p.potId,
                      layout: layout,
                    ),
                  )
                : PlantSprite(
                    catalog: widget.catalog,
                    slots: p.slots,
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
                  _dragAt = garden.anchorOf(p);
                  _dropPot = p.potId;
                  _dropRot = p.rot;
                  _dropAt = p.cell;
                  _dropOk = true;
                });
              },
              onScaleUpdate: (d) {
                if (d.pointerCount == 1) {
                  // 손가락 이동을 확대율로 나눠 그림 좌표로 되돌립니다. 칸이 아니라
                  // 기준점을 들고 다녀야 반 칸 미만의 움직임이 버려지지 않습니다.
                  final now = (_dragAt ?? garden.anchorOf(p)) +
                      d.focalPointDelta * _sceneScale;
                  final c = grid.cellAt(now);
                  final ok =
                      garden.fits(c, p.potId, rot: p.rot, ignore: p.id);
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
                _dropPot = null;
                _dropRot = null;
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

  void _say(String text) {
    final m = ScaffoldMessenger.maybeOf(context);
    m?.hideCurrentSnackBar();
    m?.showSnackBar(SnackBar(
        content: Text(text), duration: const Duration(milliseconds: 1400)));
  }

  /// 자리 하나를 나타내는 칩. 누르면 그 자리에 맞는 식물만 보여 줍니다.
  Widget _slotChip(PlacedPlant p, int k) {
    final slot = widget.catalog.pots[p.potId]!.slots[k];
    final here = p.slots[k];
    final name = here == null
        ? '비었음'
        : widget.catalog.names[here] ?? here;
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: GestureDetector(
        onTap: () => _slotSheet(p, k),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
          decoration: BoxDecoration(
            color: _card,
            borderRadius: BorderRadius.circular(11),
            border: Border.all(
                color: here == null ? const Color(0xFFE2E2DD) : _leaf,
                width: here == null ? 1 : 2),
          ),
          child: Text(
              '${k + 1} · ${widget.catalog.names[slot.grade] ?? slot.grade} 자리'
              ' — $name',
              style: TextStyle(
                  fontSize: 12.5,
                  color: here == null ? _mut : _ink,
                  fontWeight: here == null ? FontWeight.w400 : FontWeight.w700)),
        ),
      ),
    );
  }

  /// 자리 하나에 심거나 비웁니다.
  ///
  /// 등급이 맞는 식물만 보여 줍니다. 안 맞는 것을 눌러 놓고 거절당하는
  /// 것보다, 애초에 들어갈 수 있는 것만 보이는 편이 낫습니다.
  void _slotSheet(PlacedPlant p, int k) {
    final slot = widget.catalog.pots[p.potId]!.slots[k];
    final ok = widget.catalog.plants.keys.where((n) => n == slot.grade);
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: const Color(0xFFF7F7F2),
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${k + 1}번 자리 — '
                  '${widget.catalog.names[slot.grade] ?? slot.grade}만 들어갑니다',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w800, color: _ink)),
              const SizedBox(height: 12),
              Row(
                children: [
                  for (final n in ok)
                    Expanded(
                      child: _pick(
                        label: widget.catalog.names[n] ?? n,
                        asset: widget.catalog.plants[n]!.path,
                        onTap: () {
                          garden.plantInto(p, k, n);
                          Navigator.pop(context);
                        },
                      ),
                    ),
                  if (p.slots[k] != null)
                    Expanded(
                      child: TextButton(
                        onPressed: () {
                          garden.plantInto(p, k, null);
                          Navigator.pop(context);
                        },
                        child: const Text('비우기'),
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

  /// 고른 그릇에 따라 바뀌는 아래 판.
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
                      Text(widget.catalog.names[p.potId] ?? p.potId,
                          style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: _ink)),
                      const SizedBox(width: 10),
                      // 늘어나는 자식은 하나만 둡니다. Expanded 와 Spacer 를
                      // 같이 쓰면 남는 자리를 둘이 나눠 가져 칩이 잘립니다.
                      Expanded(
                        child: p.isFurniture
                            ? const Text('아직 심는 자리가 없는 가구입니다',
                                style: TextStyle(color: _mut, fontSize: 12.5))
                            : SingleChildScrollView(
                                scrollDirection: Axis.horizontal,
                                child: Row(children: [
                                  for (var k = 0; k < p.slots.length; k++)
                                    _slotChip(p, k),
                                ]),
                              ),
                      ),
                      const SizedBox(width: 6),
                      IconButton(
                          onPressed: () {
                            if (!garden.turn(p)) _say('돌리면 옆 칸을 침범합니다');
                          },
                          icon: const Icon(Icons.rotate_90_degrees_cw_outlined,
                              size: 19),
                          tooltip: '돌리기',
                          color: _ink),
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

  /// 지금 노리는 칸들. 두 칸짜리 조각은 두 칸 모두 칠합니다.
  final List<Cell> mark;

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

    if (mark.isEmpty) return;
    final tint = markOk ? const Color(0xFF4E8C5E) : const Color(0xFFB4503F);
    final fill = Paint()..color = tint.withValues(alpha: .24);
    final edge = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.4
      ..color = tint.withValues(alpha: .85);
    for (final c in mark) {
      final path = grid.diamond(c);
      canvas.drawPath(path, fill);
      canvas.drawPath(path, edge);
    }
  }

  @override
  bool shouldRepaint(_StagePainter o) =>
      o.strong != strong ||
      o.markOk != markOk ||
      !listEquals(o.mark, mark) ||
      !setEquals(o.taken, taken);
}
