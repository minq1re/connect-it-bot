import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../widgets/bottom_nav_bar.dart';
import 'candidates_screen.dart';
import 'matches_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.apiService});

  final ApiService apiService;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 1;

  @override
  Widget build(BuildContext context) {
    final List<Widget> pages = <Widget>[
      ProfileScreen(apiService: widget.apiService),
      CandidatesScreen(apiService: widget.apiService),
      const MatchesScreen(),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: pages),
      bottomNavigationBar: BottomNavBar(
        currentIndex: _currentIndex,
        onTap: (int index) {
          if (index == 2) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Мэтчи скоро появятся')),
            );
            return;
          }
          setState(() => _currentIndex = index);
        },
      ),
    );
  }
}
