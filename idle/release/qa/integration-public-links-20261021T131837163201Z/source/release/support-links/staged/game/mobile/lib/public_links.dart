import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'help_content.dart';
import 'palette.dart';
import 'presentation.dart';
import 'public_links_model.dart';

export 'public_links_model.dart';

typedef PublicPageLauncher = Future<bool> Function(Uri url);

Future<bool> launchPublicPage(Uri url) =>
    launchUrl(url, mode: LaunchMode.externalApplication);

/// A user-initiated browser handoff. This never submits a support or deletion
/// request, changes game data, or claims that the remote page is available.
class PublicLinksPanel extends StatefulWidget {
  const PublicLinksPanel({super.key, this.configuration, this.launcher});
  final PublicLinksConfig? configuration;
  final PublicPageLauncher? launcher;

  @override
  State<PublicLinksPanel> createState() => _PublicLinksPanelState();
}

class _PublicLinksPanelState extends State<PublicLinksPanel> {
  late final _environment = PublicLinksConfig.fromEnvironment();
  PublicPage? _opening;
  PublicPage? _failed;

  Future<void> _open(PublicPage page, Uri url) async {
    if (_opening != null) return;
    setState(() {
      _opening = page;
      _failed = null;
    });
    var opened = false;
    try {
      opened = await (widget.launcher ?? launchPublicPage)(url);
    } catch (_) {
      // Platform errors stay local; neither credentials nor URL errors are
      // included in telemetry, a support request, or a raw exception message.
    }
    if (!mounted) return;
    setState(() {
      _opening = null;
      _failed = opened ? null : page;
    });
  }

  @override
  Widget build(BuildContext context) {
    final config = widget.configuration ?? _environment;
    if (config.isEmpty) {
      return const LocalizedText(
        HelpCopy.externalUnavailable,
        key: ValueKey('public-pages-unconfigured'),
        style: TextStyle(color: TideColors.muted),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Semantics(
          header: true,
          child: LocalizedText('Public help pages'),
        ),
        const SizedBox(height: 12),
        const LocalizedText(
          'These pages open in your browser. Opening a page does not send a support message or delete an account.',
        ),
        const SizedBox(height: 12),
        for (final page in PublicPage.values) ...[
          if (config[page] case final url?) ...[
            OutlinedButton(
              key: ValueKey('public-page-${page.name}'),
              style: OutlinedButton.styleFrom(minimumSize: const Size(48, 56)),
              onPressed: _opening == null ? () => _open(page, url) : null,
              child: LocalizedText(switch (page) {
                PublicPage.support => 'Open support page',
                PublicPage.privacy => 'Open privacy policy',
                PublicPage.deletion => 'Open account deletion page',
              }),
            ),
            // The exact destination is selectable and never pseudolocalized.
            SelectableText(
              url.toString(),
              key: ValueKey('public-page-address-${page.name}'),
            ),
            if (_opening == page) const LocalizedText('Opening the browser…'),
            if (_failed == page)
              const Semantics(
                liveRegion: true,
                child: LocalizedText(
                  'The device did not confirm opening the page. Try again or copy the address into your browser.',
                ),
              ),
          ] else
            LocalizedText(switch (page) {
              PublicPage.support =>
                'The public support page is not configured.',
              PublicPage.privacy =>
                'The public privacy policy is not configured.',
              PublicPage.deletion =>
                'The public account deletion page is not configured.',
            }),
          const SizedBox(height: 16),
        ],
      ],
    );
  }
}
