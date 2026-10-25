/// Operator-owned public destinations, read only from build configuration.
/// No account identifiers, credentials or game data are appended to a URL.
enum PublicPage { support, privacy, deletion }

class PublicLinksConfig {
  PublicLinksConfig({
    String support = '',
    String privacy = '',
    String deletion = '',
  }) : _urls = Map.unmodifiable({
         PublicPage.support: _parse(support),
         PublicPage.privacy: _parse(privacy),
         PublicPage.deletion: _parse(deletion),
       });

  factory PublicLinksConfig.fromEnvironment() => PublicLinksConfig(
    support: const String.fromEnvironment('TIDEGLASS_SUPPORT_URL'),
    privacy: const String.fromEnvironment('TIDEGLASS_PRIVACY_URL'),
    deletion: const String.fromEnvironment('TIDEGLASS_DELETION_URL'),
  );

  final Map<PublicPage, Uri?> _urls;
  Uri? operator [](PublicPage page) => _urls[page];
  bool get isEmpty => _urls.values.every((url) => url == null);

  static Uri? _parse(String value) {
    // Only plain public HTTPS destinations are supported. Tracking queries,
    // fragments, credentials, alternate ports and local/IP hosts fail closed.
    // Reject normalization too, so a configured address is exactly the address
    // displayed and supplied to the browser. Encoded controls are not routes.
    if (value.isEmpty ||
        value.length > 2048 ||
        (RegExp(r'[\s\x00-\x1f\x7f\\]').hasMatch(value) ||
            RegExp(
              r'%(?:0[0-9a-f]|1[0-9a-f]|7f|5c)',
              caseSensitive: false,
            ).hasMatch(value))) {
      return null;
    }
    final uri = Uri.tryParse(value);
    if (uri == null ||
        uri.toString() != value ||
        uri.scheme != 'https' ||
        !uri.hasAuthority ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment ||
        (uri.hasPort && uri.port != 443)) {
      return null;
    }
    final host = uri.host;
    final labels = host.split('.');
    if (host.length > 253 ||
        labels.length < 2 ||
        labels.any(
          (part) =>
              !RegExp(r'^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$').hasMatch(part),
        ) ||
        !RegExp(r'^[a-z]{2,63}$').hasMatch(labels.last) ||
        const {
          'localhost',
          'local',
          'internal',
          'invalid',
          'test',
        }.contains(labels.last)) {
      return null;
    }
    return uri;
  }
}
