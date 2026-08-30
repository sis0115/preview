import 'package:flutter/material.dart';

import 'catalog.dart';
import 'greenhouse_page.dart';

void main() => runApp(const KitApp());

class KitApp extends StatelessWidget {
  const KitApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: '우리집 온실',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(useMaterial3: true, fontFamily: 'Pretendard'),
        home: const _Boot(),
      );
}

/// 카탈로그를 읽고 나서 화면을 엽니다.
///
/// 기준점과 격자 규격이 catalog.json 에 있어, 그림을 갈아 끼워도 코드는
/// 그대로입니다 — 자르기 도구만 다시 돌리면 됩니다.
class _Boot extends StatefulWidget {
  const _Boot();

  @override
  State<_Boot> createState() => _BootState();
}

class _BootState extends State<_Boot> {
  late final Future<Catalog> _catalog = Catalog.load();

  @override
  Widget build(BuildContext context) => FutureBuilder<Catalog>(
        future: _catalog,
        builder: (context, snap) {
          if (snap.hasError) {
            return Scaffold(
              backgroundColor: const Color(0xFFF5F5EF),
              body: Center(
                child: Padding(
                  padding: const EdgeInsets.all(28),
                  child: Text('에셋을 불러오지 못했습니다.\n${snap.error}',
                      textAlign: TextAlign.center),
                ),
              ),
            );
          }
          if (!snap.hasData) {
            return const Scaffold(
              backgroundColor: Color(0xFFF5F5EF),
              body: Center(
                child: SizedBox(
                    width: 26,
                    height: 26,
                    child: CircularProgressIndicator(strokeWidth: 2.4)),
              ),
            );
          }
          return GreenhousePage(catalog: snap.data!);
        },
      );
}
