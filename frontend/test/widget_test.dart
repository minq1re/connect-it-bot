import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';
import 'package:frontend/screens/welcome_screen.dart';

void main() {
  testWidgets('App shows welcome screen first', (WidgetTester tester) async {
    await tester.pumpWidget(const ConnectItApp());
    expect(find.byType(WelcomeScreen), findsOneWidget);
    expect(find.text('ConnectIT'), findsOneWidget);
  });
}
