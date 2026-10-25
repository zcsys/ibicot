import 'source/release/support-links/staged/game/mobile/lib/public_links_model.dart';
void main() {
  var checks=0;
  void check(bool value,String label) {checks++; if(!value) throw StateError(label);}
  for(final bad in ['https://EXAMPLE.COM/help','https://example.com:443/help','https://example.com/a/../help','https://example.com/%2e%2e/help','https://example.com/a/./help','https://example.com/%0ahelp','https://example.com/%0Ahelp','https://example.com/%5chelp','https://example.com/%5Chelp','https://example.com/%1fhelp','https://example.com/%7Fhelp','http://example.com/help','https://user:secret@example.com/help','https://example.com/help?','https://example.com/help#','https://127.0.0.1/help','https://[::1]/help','https://example.com:8443/help','https://example.com/help\n']) {
    check(PublicLinksConfig(support:bad).isEmpty,'reject $bad');
  }
  for(final good in ['https://example.com/help','https://example.com/help%20page','https://support.example.com/privacy-policy']) {
    final config=PublicLinksConfig(support:good,privacy:'http://bad.invalid');
    check(config[PublicPage.support].toString()==good,'exact $good');
    check(config[PublicPage.privacy]==null && config[PublicPage.deletion]==null,'partial');
  }
  check(PublicLinksConfig.fromEnvironment().isEmpty,'default disabled');
  print('$checks independent canonical URL assertions passed');
}
