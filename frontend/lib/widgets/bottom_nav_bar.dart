import 'package:flutter/material.dart';

class BottomNavBar extends StatelessWidget {
  const BottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  final int currentIndex;
  final ValueChanged<int> onTap;

  static const Color _iconColor = Color(0xFF555B6E);
  static const Color _activeColor = Color(0xFFC27D7D);

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: currentIndex,
      onTap: onTap,
      type: BottomNavigationBarType.fixed,
      backgroundColor: Colors.white,
      selectedItemColor: _activeColor,
      unselectedItemColor: _iconColor,
      showSelectedLabels: false,
      showUnselectedLabels: false,
      items: const <BottomNavigationBarItem>[
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline, color: _iconColor),
          activeIcon: Icon(Icons.person, color: _activeColor),
          label: 'Профиль',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.home_outlined, color: _iconColor),
          activeIcon: Icon(Icons.home, color: _activeColor),
          label: 'Поиск',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.favorite_border, color: _iconColor),
          activeIcon: Icon(Icons.favorite, color: _activeColor),
          label: 'Мэтчи',
        ),
      ],
    );
  }
}
