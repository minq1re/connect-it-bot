import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';

void main() {
  testWidgets('App renders profile screen', (WidgetTester tester) async {
    await tester.pumpWidget(const ConnectItApp());
    expect(find.byType(ConnectItApp), findsOneWidget);
  });
}
