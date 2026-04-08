import 'dart:js' as js;

/// Разворачивает мини-приложение на весь экран (рекомендуется в Telegram WebApp).
void expandTelegramWebApp() {
  try {
    js.context.callMethod('eval', <String>[
      'try{Telegram&&Telegram.WebApp&&Telegram.WebApp.expand()}catch(e){}',
    ]);
  } catch (_) {}
}

/// Есть ли объект Telegram.WebApp (открыто внутри Telegram).
bool isTelegramWebAppContext() {
  try {
    final dynamic telegram = js.context['Telegram'];
    if (telegram == null) return false;
    final dynamic webApp = telegram['WebApp'];
    return webApp != null;
  } catch (_) {
    return false;
  }
}
