import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/telegram_init_data.dart';
import '../services/telegram_web_expand.dart';
import 'profile_form_screen.dart';

/// Стартовый экран: данные Telegram на backend не уходят, пока пользователь
/// не нажмёт «Продолжить через Telegram» и не перейдёт к анкете.
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key, required this.apiService});

  final ApiService apiService;

  static const Color _bgColor = Color(0xFF89B0AE);
  static const Color _textColor = Color(0xFF555B6E);
  static const Color _buttonColor = Color(0xFFBEE3DB);

  void _onContinue(BuildContext context) {
    expandTelegramWebApp();

    final String initData = getTelegramInitData();
    if (initData.isEmpty && !isTelegramWebAppContext()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Откройте приложение через кнопку в Telegram, либо задайте '
            'TELEGRAM_INIT_DATA при локальной отладке.',
          ),
        ),
      );
      return;
    }

    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (BuildContext context) =>
            ProfileFormScreen(apiService: apiService),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bgColor,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (BuildContext context, BoxConstraints constraints) {
            final double w = constraints.maxWidth;
            final double h = constraints.maxHeight;
            final double pad = w * 0.08;

            return Center(
              child: SingleChildScrollView(
                padding: EdgeInsets.symmetric(
                  horizontal: pad,
                  vertical: h * 0.04,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text(
                      'ConnectIT',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: _textColor,
                        fontSize: w * 0.12,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.5,
                      ),
                    ),
                    SizedBox(height: h * 0.02),
                    Text(
                      'Найди своего наставника в IT',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: _textColor,
                        fontSize: w * 0.045,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    SizedBox(height: h * 0.06),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _buttonColor,
                          foregroundColor: _textColor,
                          elevation: 0,
                          padding: EdgeInsets.symmetric(
                            vertical: h * 0.022,
                            horizontal: w * 0.06,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                          textStyle: TextStyle(
                            fontSize: w * 0.042,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        onPressed: () => _onContinue(context),
                        child: const Text(
                          'Продолжить через Telegram',
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
