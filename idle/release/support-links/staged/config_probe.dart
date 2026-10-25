import 'game/mobile/lib/public_links_model.dart';
void main() {
  var checks = 0;
  void check(bool value, String name) { checks++; if (!value) throw StateError(name); }
  for (final bad in ['', 'http://example.com', 'https://user:secret@example.com', 'https://example.com?token=secret', 'https://example.com#token', 'https://example.com?', 'https://example.com#', 'https://localhost', 'https://127.0.0.1', 'https://[::1]', 'https://example.local', 'https://example.test', 'https://example.invalid', 'https://example.com:8443', ' https://example.com', 'https://bad_host.com', 'https://-bad.com', 'https://example..com', 'https://EXAMPLE.COM/help', 'https://example.com:443/privacy', 'https://example.com/a/../help', 'https://example.com/%2e%2e/help', 'https://example.com/%0a', 'https://example.com/%5c']) {
    check(PublicLinksConfig(support: bad).isEmpty, 'reject $bad');
  }
  final good = PublicLinksConfig(support: 'https://example.com/support', privacy: 'https://example.com/privacy');
  check(good[PublicPage.support].toString() == 'https://example.com/support', 'exact');
  check(good[PublicPage.privacy] != null && good[PublicPage.deletion] == null, 'independent destinations');
  check(PublicLinksConfig.fromEnvironment().isEmpty, 'default disabled');
  print('$checks configuration assertions passed');
}
