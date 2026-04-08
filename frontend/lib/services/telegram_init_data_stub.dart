String getTelegramInitData() {
  return const String.fromEnvironment('TELEGRAM_INIT_DATA', defaultValue: '');
}
