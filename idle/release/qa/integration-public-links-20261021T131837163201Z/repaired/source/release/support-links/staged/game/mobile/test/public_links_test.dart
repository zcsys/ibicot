import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/help_content.dart';
import 'package:tideglass/help_screen.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/public_links.dart';

void main() {
  final config = PublicLinksConfig(
    support: 'https://example.com/support',
    privacy: 'https://example.com/privacy',
    deletion: 'https://example.com/account-deletion',
  );
  Future<void> show(WidgetTester tester, Widget child) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    tester.platformDispatcher.textScaleFactorTestValue = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    await tester.pumpWidget(MaterialApp(theme: tideglassTheme(), home: child));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  Future<void> tap(WidgetTester tester, String key) async {
    final finder = find.byKey(ValueKey(key));
    await Scrollable.ensureVisible(tester.element(finder), alignment: .5);
    await tester.pumpAndSettle();
    final rect = tester.getRect(finder);
    final scrollable = Scrollable.of(tester.element(finder));
    final viewport = tester.getRect(find.byWidget(scrollable.widget));
    expect(rect.height, greaterThanOrEqualTo(48));
    expect(rect.width, greaterThanOrEqualTo(48));
    expect(viewport.contains(rect.topLeft + const Offset(.1, .1)), isTrue);
    expect(viewport.contains(rect.bottomRight - const Offset(.1, .1)), isTrue);
    for (final point in [
      rect.center,
      rect.topCenter + const Offset(0, 1),
      rect.bottomCenter - const Offset(0, 1),
      rect.centerLeft + const Offset(1, 0),
      rect.centerRight - const Offset(1, 0),
    ]) {
      expect(
        finder.hitTestable(
          at: Alignment(
            (point.dx - rect.center.dx) / (rect.width / 2),
            (point.dy - rect.center.dy) / (rect.height / 2),
          ),
        ),
        findsOneWidget,
      );
    }
    await tester.tap(finder);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  test(
    'configuration fails closed and preserves exact public destinations',
    () {
      expect(PublicLinksConfig().isEmpty, isTrue);
      for (final value in [
        '',
        'http://example.com',
        'javascript:alert(1)',
        'https://user:secret@example.com',
        'https://example.com?token=secret',
        'https://example.com#token',
        'https://example.com?',
        'https://example.com#',
        'https://localhost',
        'https://127.0.0.1',
        'https://[::1]',
        'https://example.local',
        'https://example.test',
        'https://example.invalid',
        'https://example.com:8443',
        ' https://example.com',
        'https://example.com\n',
        'https://bad_host.com',
        'https://-bad.com',
        'https://example.com\\evil',
        'https://example.com/${'x' * 2048}',
        'https://example..com',
        'https://EXAMPLE.COM/help',
        'https://example.com:443/privacy',
        'https://example.com/a/../help',
        'https://example.com/%2e%2e/help',
        'https://example.com/%0a',
        'https://example.com/%5c',
      ]) {
        final rejected = PublicLinksConfig(support: value);
        expect(rejected.isEmpty, isTrue, reason: value);
      }
      expect(
        config[PublicPage.support].toString(),
        'https://example.com/support',
      );
      expect(
        PublicLinksConfig(
          privacy: 'https://example.com/privacy',
        )[PublicPage.privacy],
        isNotNull,
      );
    },
  );

  testWidgets('default missing configuration never calls a launcher', (
    tester,
  ) async {
    var calls = 0;
    await show(
      tester,
      HelpScreen(
        initialTopic: HelpTopic.privacy,
        publicLinks: PublicLinksConfig(),
        publicPageLauncher: (_) async {
          calls++;
          return true;
        },
      ),
    );
    expect(
      find.byKey(const ValueKey('public-pages-unconfigured')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('public-page-support')), findsNothing);
    expect(calls, 0);
  });

  testWidgets(
    'all three real help actions launch only the exact selected URL',
    (tester) async {
      final opened = <Uri>[];
      await show(
        tester,
        HelpScreen(
          initialTopic: HelpTopic.privacy,
          publicLinks: config,
          publicPageLauncher: (url) async {
            opened.add(url);
            return true;
          },
        ),
      );
      expect(opened, isEmpty);
      expect(
        find.text(Presentation.text(HelpCopy.externalUnavailable)),
        findsNothing,
      );
      for (final page in PublicPage.values) {
        expect(find.text(config[page].toString()), findsOneWidget);
        await tap(tester, 'public-page-${page.name}');
        expect(opened.last, config[page]);
      }
      expect(opened.length, 3);
      await tap(tester, 'help-all-topics');
      await tap(tester, 'help-topic-recovery');
      await tap(tester, 'public-page-deletion');
      expect(opened.length, 4);
      expect(opened.last, config[PublicPage.deletion]);
    },
  );

  testWidgets(
    'partial configuration has no inactive fake links and failure is retryable',
    (tester) async {
      var attempts = 0;
      await show(
        tester,
        HelpScreen(
          initialTopic: HelpTopic.privacy,
          publicLinks: PublicLinksConfig(
            support: 'https://example.com/support',
            privacy: 'http://unsafe.invalid',
          ),
          publicPageLauncher: (_) async {
            attempts++;
            if (attempts == 1) throw StateError('private detail');
            return false;
          },
        ),
      );
      expect(find.byKey(const ValueKey('public-page-privacy')), findsNothing);
      expect(find.byKey(const ValueKey('public-page-deletion')), findsNothing);
      await tap(tester, 'public-page-support');
      expect(find.textContaining('private detail'), findsNothing);
      expect(
        find.text(
          Presentation.text(
            'The device did not confirm opening the page. Try again or copy the address into your browser.',
          ),
        ),
        findsOneWidget,
      );
      await tap(tester, 'public-page-support');
      expect(attempts, 2);
    },
  );

  testWidgets(
    'one pending browser handoff cannot dispatch another and dispose is safe',
    (tester) async {
      var calls = 0;
      final pending = Completer<bool>();
      await show(
        tester,
        HelpScreen(
          initialTopic: HelpTopic.privacy,
          publicLinks: config,
          publicPageLauncher: (_) {
            calls++;
            return pending.future;
          },
        ),
      );
      await tap(tester, 'public-page-support');
      for (final page in PublicPage.values) {
        final button = tester.widget<OutlinedButton>(
          find.byKey(ValueKey('public-page-${page.name}')),
        );
        expect(button.onPressed, isNull);
      }
      expect(calls, 1);
      await tester.pumpWidget(const SizedBox());
      pending.complete(true);
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    },
  );
}
