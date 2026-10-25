import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass/help_content.dart';
import 'package:tideglass/help_screen.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  void narrow(WidgetTester tester) {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    tester.platformDispatcher.textScaleFactorTestValue = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  Future<void> show(WidgetTester tester, HelpScreen screen) async {
    await tester.pumpWidget(
      MaterialApp(
        key: UniqueKey(),
        debugShowCheckedModeBanner: false,
        theme: tideglassTheme(),
        home: screen,
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  Future<void> reveal(WidgetTester tester, Finder finder) async {
    await Scrollable.ensureVisible(tester.element(finder), alignment: .5);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  Future<void> tap(WidgetTester tester, Finder finder) async {
    await reveal(tester, finder);
    expect(tester.getRect(finder).height, greaterThanOrEqualTo(48));
    await tester.tap(finder);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  test('stable unique topics and immutable English content', () {
    expect(
      HelpContent.articles.map((a) => a.topic).toSet(),
      HelpTopic.values.toSet(),
    );
    final ids = HelpContent.articles
        .expand((a) => a.sections)
        .map((s) => s.id)
        .toList();
    expect(ids.toSet().length, ids.length);
    expect(() => HelpContent.articles.clear(), throwsUnsupportedError);
    expect(
      () => HelpContent.articles.first.sections.clear(),
      throwsUnsupportedError,
    );
    expect(
      () => HelpContent.articles.first.sections.first.paragraphs.clear(),
      throwsUnsupportedError,
    );
    final text = HelpContent.articles
        .expand((a) => a.sections)
        .expand((s) => s.paragraphs)
        .join(' ');
    for (final required in [
      '100 Survey Notes once',
      '50 Survey Notes',
      'first 24 hours',
      'next 48 hours',
      'after 72 hours',
      'six slots per account day',
      'does not combine wallets',
      'cannot recover the account',
    ]) {
      expect(text, contains(required));
    }
    expect(text, isNot(contains('https://')));
    expect(
      HelpCopy.developmentVersion,
      File(
        'pubspec.yaml',
      ).readAsStringSync().split('version: ')[1].split('\n')[0],
    );
  });
  testWidgets('all eight real routes and sections readable at 320px 200%', (
    tester,
  ) async {
    narrow(tester);
    final semantics = tester.ensureSemantics();
    await show(tester, const HelpScreen());
    for (final article in HelpContent.articles) {
      await tap(
        tester,
        find.byKey(ValueKey('help-topic-${article.topic.name}')),
      );
      expect(
        find.byKey(ValueKey('help-summary-${article.topic.name}')),
        findsOneWidget,
      );
      expect(find.text(Presentation.text(article.title)), findsOneWidget);
      for (final section in article.sections) {
        final heading = find.byKey(ValueKey('help-section-${section.id}'));
        await reveal(tester, heading);
        expect(tester.getSemantics(heading).flagsCollection.isHeader, isTrue);
      }
      await tap(tester, find.byKey(const ValueKey('help-all-topics')));
      final index = find.byKey(const ValueKey('help-topic-play'));
      expect(Navigator.of(tester.element(index)).canPop(), isFalse);
      expect(tester.takeException(), isNull);
    }
    semantics.dispose();
  });
  testWidgets(
    'only supplied real account recovery and privacy actions appear',
    (tester) async {
      narrow(tester);
      await show(tester, const HelpScreen(initialTopic: HelpTopic.recovery));
      expect(find.byKey(const ValueKey('help-action-account')), findsNothing);
      expect(
        find.byKey(const ValueKey('help-action-localRecovery')),
        findsNothing,
      );
      await tap(tester, find.byKey(const ValueKey('help-all-topics')));
      expect(find.byKey(const ValueKey('help-topic-privacy')), findsOneWidget);
      var recovery = 0, account = 0, privacy = 0;
      await show(
        tester,
        HelpScreen(
          initialTopic: HelpTopic.recovery,
          onOpenAccount: () => account++,
          onOpenLocalRecovery: () => recovery++,
        ),
      );
      await tap(
        tester,
        find.byKey(const ValueKey('help-action-localRecovery')),
      );
      await tap(tester, find.byKey(const ValueKey('help-action-account')));
      expect([recovery, account], [1, 1]);
      await show(
        tester,
        HelpScreen(
          initialTopic: HelpTopic.privacy,
          onOpenPrivacySettings: () => privacy++,
        ),
      );
      await tap(
        tester,
        find.byKey(const ValueKey('help-action-privacySettings')),
      );
      expect(privacy, 1);
      expect(
        find.text(Presentation.text(HelpCopy.externalUnavailable)),
        findsOneWidget,
      );
    },
  );
  testWidgets('credits open actual bundled software licenses', (tester) async {
    narrow(tester);
    await show(tester, const HelpScreen(initialTopic: HelpTopic.credits));
    await tap(tester, find.byKey(const ValueKey('help-action-licenses')));
    expect(find.byType(LicensePage), findsOneWidget);
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(
      find.byKey(const ValueKey('help-section-development-credit')),
      findsOneWidget,
    );
  });
  testWidgets(
    'actual Logbook and settings open help and existing local export',
    (tester) async {
      narrow(tester);
      final game = GameController(
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 19, 12),
      );
      addTearDown(game.dispose);
      final before = game.state.toJson();
      var exports = 0, imports = 0;
      await tester.pumpWidget(
        TideglassApp(
          controller: game,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
          onExport: () async {
            exports++;
            return 'unmodified-local-export';
          },
          onImport: (_) async {
            imports++;
          },
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byType(NavigationDestination).at(2));
      await tester.pumpAndSettle();
      await tap(tester, find.byKey(const ValueKey('open-handbook')));
      await tap(tester, find.byKey(const ValueKey('help-topic-recovery')));
      await tap(
        tester,
        find.byKey(const ValueKey('help-action-localRecovery')),
      );
      final exportLabel = find.text(Presentation.text(UiCopy.exportMyHarbor));
      await reveal(tester, exportLabel);
      await tester.tap(exportLabel);
      await tester.pumpAndSettle();
      expect(exports, 1);
      expect(imports, 0);
      expect(find.text('unmodified-local-export'), findsOneWidget);
      expect(game.state.toJson(), before);
      await tester.pumpWidget(const SizedBox());
      await tester.pumpWidget(
        TideglassApp(
          controller: game,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.tune_rounded));
      await tester.pumpAndSettle();
      await tap(tester, find.byKey(const ValueKey('open-handbook-settings')));
      expect(find.byKey(const ValueKey('help-topic-play')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('capture production help at expanded size', (tester) async {
    narrow(tester);
    await tester.runAsync(() async {
      for (final entry in {
        'Roboto': 'Roboto-Regular.ttf',
        'MaterialIcons': 'MaterialIcons-Regular.otf',
      }.entries) {
        final file = File(
          '../../.tooling/flutter/bin/cache/artifacts/material_fonts/${entry.value}',
        );
        await (FontLoader(
          entry.key,
        )..addFont(file.readAsBytes().then(ByteData.sublistView))).load();
      }
    });
    final boundaryKey = GlobalKey();
    for (final topic in [
      HelpTopic.notes,
      HelpTopic.recovery,
      HelpTopic.privacy,
    ]) {
      await tester.pumpWidget(
        RepaintBoundary(
          key: boundaryKey,
          child: MaterialApp(
            key: ValueKey(topic),
            debugShowCheckedModeBanner: false,
            theme: tideglassTheme(),
            home: HelpScreen(initialTopic: topic),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      final boundary =
          boundaryKey.currentContext!.findRenderObject()!
              as RenderRepaintBoundary;
      await tester.runAsync(() async {
        final image = await boundary.toImage(pixelRatio: 2);
        final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
        final file = File(
          '../../release/help-proof/${Presentation.pseudoEnabled ? 'pseudo' : 'english'}-${topic.name}.png',
        );
        await file.parent.create(recursive: true);
        await file.writeAsBytes(bytes!.buffer.asUint8List());
        image.dispose();
      });
    }
  });
}
