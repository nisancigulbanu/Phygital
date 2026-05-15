import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/main.dart';

void main() {
  testWidgets('home screen renders both entry points', (tester) async {
    await tester.pumpWidget(const PhygitalApp());

    expect(find.text('Phygital Fashion Advisor'), findsOneWidget);
    expect(find.text('Etiketi Tara'), findsOneWidget);
    await tester.drag(find.byType(Scrollable), const Offset(0, -300));
    await tester.pumpAndSettle();
    expect(find.text('Online Urun Ekle'), findsOneWidget);
  });
}
