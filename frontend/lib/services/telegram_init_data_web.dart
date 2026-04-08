import 'dart:js' as js;

String getTelegramInitData() {
  final String fallback = const String.fromEnvironment(
    'TELEGRAM_INIT_DATA',
    defaultValue: '',
  );

  try {
    final dynamic telegram = js.context['Telegram'];
    if (telegram == null) return fallback;

    final dynamic webApp = telegram['WebApp'];
    if (webApp == null) return fallback;

    final dynamic initData = webApp['initData'];
    if (initData is String && initData.isNotEmpty) {
      return initData;
    }
  } catch (_) {
    // Если Telegram WebApp JS API недоступен, используем fallback.
  }

  return fallback;
}
