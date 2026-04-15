import 'package:flutter/material.dart';

class MatchesScreen extends StatelessWidget {
  const MatchesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFF89B0AE),
      body: Center(
        child: Text(
          'Экран мэтчей скоро появится',
          style: TextStyle(
            color: Color(0xFF555B6E),
            fontSize: 22,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}
