import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'services/api_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ConnectItApp());
}

class ConnectItApp extends StatelessWidget {
  const ConnectItApp({super.key});

  @override
  Widget build(BuildContext context) {
    final ApiService apiService = ApiService();
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'ConnectIT',
      theme: ThemeData(useMaterial3: true, fontFamily: 'Roboto'),
      home: HomeScreen(apiService: apiService),
    );
  }
}
