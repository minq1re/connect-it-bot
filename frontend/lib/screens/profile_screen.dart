import 'package:flutter/material.dart';

import '../services/api_service.dart';
import 'profile_form_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key, required this.apiService});

  final ApiService apiService;

  @override
  Widget build(BuildContext context) {
    return ProfileFormScreen(apiService: apiService);
  }
}
