import 'package:flutter/material.dart';

import 'help_content.dart';
import 'palette.dart';
import 'presentation.dart';
import 'public_links.dart';

/// Read-only help. Optional host actions open existing account/recovery flows;
/// this screen never creates accounts, changes consent, imports or resets saves.
class HelpScreen extends StatelessWidget {
  const HelpScreen({
    super.key,
    this.initialTopic,
    this.onOpenAccount,
    this.onOpenLocalRecovery,
    this.onOpenPrivacySettings,
    this.publicLinks,
    this.publicPageLauncher,
  }) : _indexBelow = false;
  const HelpScreen._fromIndex({
    required this.initialTopic,
    this.onOpenAccount,
    this.onOpenLocalRecovery,
    this.onOpenPrivacySettings,
    this.publicLinks,
    this.publicPageLauncher,
  }) : _indexBelow = true;
  final PublicLinksConfig? publicLinks;
  final PublicPageLauncher? publicPageLauncher;
  final bool _indexBelow;
  final HelpTopic? initialTopic;
  final VoidCallback? onOpenAccount, onOpenLocalRecovery, onOpenPrivacySettings;

  void _open(BuildContext context, HelpTopic? topic) {
    final navigator = Navigator.of(context);
    if (topic == null) {
      if (_indexBelow) {
        navigator.pop();
      } else {
        navigator.pushReplacement(
          MaterialPageRoute<void>(
            builder: (_) => HelpScreen(
              onOpenAccount: onOpenAccount,
              onOpenLocalRecovery: onOpenLocalRecovery,
              onOpenPrivacySettings: onOpenPrivacySettings,
              publicLinks: publicLinks,
              publicPageLauncher: publicPageLauncher,
            ),
          ),
        );
      }
      return;
    }
    navigator.push(
      MaterialPageRoute<void>(
        builder: (_) => HelpScreen._fromIndex(
          initialTopic: topic,
          onOpenAccount: onOpenAccount,
          onOpenLocalRecovery: onOpenLocalRecovery,
          onOpenPrivacySettings: onOpenPrivacySettings,
          publicLinks: publicLinks,
          publicPageLauncher: publicPageLauncher,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final article = initialTopic == null
        ? null
        : HelpContent.article(initialTopic!);
    return Scaffold(
      appBar: readingAppBar(context, title: article?.title ?? HelpCopy.title),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 760),
            child: SingleChildScrollView(
              key: ValueKey('help-scroll-${initialTopic?.name ?? 'index'}'),
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
              child: FocusTraversalGroup(
                policy: ReadingOrderTraversalPolicy(),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: article == null
                      ? _index(context)
                      : _article(context, article),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  List<Widget> _index(BuildContext context) => [
    const LocalizedText(HelpCopy.intro),
    const SizedBox(height: 20),
    for (final article in HelpContent.articles) ...[
      OutlinedButton(
        key: ValueKey('help-topic-${article.topic.name}'),
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 64),
          padding: const EdgeInsets.all(16),
          alignment: Alignment.centerLeft,
        ),
        onPressed: () => _open(context, article.topic),
        child: LocalizedText(
          article.title,
          style: Theme.of(context).textTheme.titleMedium,
        ),
      ),
      const SizedBox(height: 8),
      LocalizedText(
        article.summary,
        style: const TextStyle(color: TideColors.muted),
      ),
      const SizedBox(height: 20),
    ],
    const SizedBox(height: 8),
    PublicLinksPanel(configuration: publicLinks, launcher: publicPageLauncher),
  ];

  List<Widget> _article(BuildContext context, HelpArticle article) => [
    LocalizedText(
      article.summary,
      key: ValueKey('help-summary-${article.topic.name}'),
      style: const TextStyle(color: TideColors.muted),
    ),
    const SizedBox(height: 24),
    for (final section in article.sections) ...[
      Semantics(
        header: true,
        child: LocalizedText(
          section.title,
          key: ValueKey('help-section-${section.id}'),
          style: Theme.of(context).textTheme.titleLarge,
        ),
      ),
      const SizedBox(height: 12),
      for (final paragraph in section.paragraphs) ...[
        LocalizedText(paragraph),
        const SizedBox(height: 16),
      ],
      const SizedBox(height: 16),
    ],
    if (article.topic == HelpTopic.releaseNotes) ...[
      const LocalizedText(HelpCopy.developmentNotice),
      const SizedBox(height: 8),
      const Text(
        HelpCopy.developmentVersion,
        key: ValueKey('help-build-version'),
      ),
      const SizedBox(height: 24),
    ],
    if (const {
      HelpTopic.privacy,
      HelpTopic.recovery,
      HelpTopic.releaseNotes,
    }.contains(article.topic)) ...[
      PublicLinksPanel(
        configuration: publicLinks,
        launcher: publicPageLauncher,
      ),
      const SizedBox(height: 24),
    ],
    for (final action in article.actions)
      if (_callback(context, action) != null) ...[
        OutlinedButton(
          key: ValueKey('help-action-${action.name}'),
          style: OutlinedButton.styleFrom(minimumSize: const Size(48, 56)),
          onPressed: _callback(context, action),
          child: LocalizedText(HelpCopy.action(action)),
        ),
        const SizedBox(height: 12),
      ],
    const SizedBox(height: 12),
    OutlinedButton.icon(
      key: const ValueKey('help-all-topics'),
      style: OutlinedButton.styleFrom(minimumSize: const Size(48, 56)),
      onPressed: () => _open(context, null),
      icon: const Icon(Icons.menu_book_outlined),
      label: const LocalizedText(HelpCopy.backToTopics),
    ),
  ];

  VoidCallback? _callback(BuildContext context, HelpAction action) =>
      switch (action) {
        HelpAction.account => onOpenAccount,
        HelpAction.localRecovery => onOpenLocalRecovery,
        HelpAction.privacySettings => onOpenPrivacySettings,
        HelpAction.licenses => () => showLicensePage(
          context: context,
          applicationName: HelpCopy.brand,
          applicationVersion: HelpCopy.developmentVersion,
        ),
      };
}
