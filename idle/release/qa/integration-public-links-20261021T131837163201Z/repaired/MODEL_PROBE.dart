import 'source/release/support-links/staged/game/mobile/lib/public_links_model.dart';
void main() {
  for (final input in [
    'https://EXAMPLE.COM/help',
    'https://example.com:443/help',
    'https://example.com/a/../help',
    'https://example.com/%2e%2e/help',
    'https://example.com/a/./help',
    'https://example.com/%0ahelp',
    'https://example.com/%5chelp',
    'https://example.com/%3Ftoken=abc',
    'https://example.com/help',
    'https://example.com/help%20page',
    'https://foo.onion/help',
    'https://foo.home.arpa/help',
  ]) {
    final actual = PublicLinksConfig(support: input)[PublicPage.support];
    print('$input => $actual; exact=${actual?.toString() == input}');
  }
}
