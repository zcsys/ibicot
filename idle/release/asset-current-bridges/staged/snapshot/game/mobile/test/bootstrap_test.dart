import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

SaveRepository repository(Directory dir) => SaveRepository(
  dir,
  economicVersion: economyVersion,
  economicDigest: bundledEconomyDigest,
  validatePayload: validateClientPayload,
);
Map<String, dynamic> payload(
  GameState state, {
  ClientPreferences prefs = const ClientPreferences(
    reduceMotion: true,
    onboardingDismissed: true,
  ),
}) => {
  'client_schema_version': 1,
  'core': state.toJson(),
  'client_preferences': prefs.toJson(),
};
Future<void> settleIo(
  WidgetTester tester, {
  required bool Function() until,
}) async {
  for (var attempt = 0; attempt < 100 && !until(); attempt++) {
    await tester.runAsync(() async {
      await Future<void>.delayed(const Duration(milliseconds: 10));
    });
    await tester.pump();
  }
  expect(
    until(),
    isTrue,
    reason:
        'Native bootstrap must settle or show a recoverable error within the test boundary. Visible text: ${tester.widgetList<Text>(find.byType(Text)).map((t) => t.data).join(" | ")}',
  );
}

void main() {
  testWidgets(
    'native bootstrap reopens actual persisted core and preferences',
    (tester) async {
      final dir = Directory.systemTemp.createTempSync(
        'tideglass-client-reopen-',
      );
      addTearDown(() => dir.deleteSync(recursive: true));
      const engine = TideglassEngine();
      final funded = engine
          .advance(GameState.initial(), const Duration(seconds: 100))
          .state;
      final bought = engine.buy(funded, 0, 1).state;
      await tester.runAsync(() async {
        final store = repository(dir);
        await store.load();
        await store.save(
          payload(
            bought,
            prefs: const ClientPreferences(
              reduceMotion: true,
              largeText: true,
              scientific: true,
              onboardingDismissed: true,
            ),
          ),
          settledThrough: DateTime.now().toUtc(),
        );
      });
      await tester.pumpWidget(
        TideglassBootstrap(directory: dir, enableAudio: false),
      );
      await settleIo(
        tester,
        until: () => find.byType(TideglassApp).evaluate().isNotEmpty,
      );
      final app = tester.widget<TideglassApp>(find.byType(TideglassApp));
      expect(app.controller.state.counts, [2, 0, 0, 0, 0]);
      expect(
        app.controller.state.lifetimeMicros,
        greaterThanOrEqualTo(bought.lifetimeMicros),
      );
      expect(app.initialPreferences.largeText, isTrue);
      expect(app.initialPreferences.scientific, isTrue);
      await tester.runAsync(() => app.controller.save());
      await tester.pumpWidget(const SizedBox());
      await tester.runAsync(() async {
        final saved = await repository(dir).load();
        expect(
          GameState.fromJson(
            Map<String, dynamic>.from(saved.snapshot!.payload['core'] as Map),
          ).counts[0],
          2,
        );
      });
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('one corrupt snapshot recovers real prior branch with notice', (
    tester,
  ) async {
    final dir = Directory.systemTemp.createTempSync('tideglass-client-backup-');
    addTearDown(() => dir.deleteSync(recursive: true));
    await tester.runAsync(() async {
      final store = repository(dir);
      await store.load();
      await store.save(
        payload(GameState.initial()),
        settledThrough: DateTime.now().toUtc(),
      );
      await store.save(
        payload(
          const TideglassEngine()
              .advance(GameState.initial(), const Duration(seconds: 10))
              .state,
        ),
        settledThrough: DateTime.now().toUtc(),
      );
      final slots = dir
          .listSync()
          .whereType<File>()
          .where((f) => RegExp(r'progress\.\d\.json$').hasMatch(f.path))
          .toList();
      slots.sort(
        (a, b) =>
            (jsonDecode(a.readAsStringSync())['envelope']['revision'] as int)
                .compareTo(
                  jsonDecode(b.readAsStringSync())['envelope']['revision']
                      as int,
                ),
      );
      slots.last.writeAsStringSync('{broken');
    });
    await tester.pumpWidget(
      TideglassBootstrap(directory: dir, enableAudio: false),
    );
    await settleIo(
      tester,
      until: () => find.byType(TideglassApp).evaluate().isNotEmpty,
    );
    expect(
      find.textContaining('previous saved harbor was recovered'),
      findsOneWidget,
    );
    await tester.runAsync(
      () => tester
          .widget<TideglassApp>(find.byType(TideglassApp))
          .controller
          .save(),
    );
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets(
    'both corrupt slots remain untouched and recovery view is honest',
    (tester) async {
      final dir = Directory.systemTemp.createTempSync(
        'tideglass-client-corrupt-',
      );
      addTearDown(() => dir.deleteSync(recursive: true));
      final first = File('${dir.path}/progress.0.json')
        ..writeAsStringSync('broken-first');
      final second = File('${dir.path}/progress.1.json')
        ..writeAsStringSync('broken-second');
      await tester.pumpWidget(
        TideglassBootstrap(directory: dir, enableAudio: false),
      );
      await settleIo(
        tester,
        until: () => find.text('Keep your harbor safe').evaluate().isNotEmpty,
      );
      expect(find.byType(TideglassApp), findsNothing);
      expect(first.readAsStringSync(), 'broken-first');
      expect(second.readAsStringSync(), 'broken-second');
      expect(
        find.textContaining('Neither saved copy could be opened'),
        findsOneWidget,
      );
      await tester.pumpWidget(const SizedBox());
    },
  );
  testWidgets(
    'explicit import replaces a branch and retains current branch archive',
    (tester) async {
      final dir = Directory.systemTemp.createTempSync(
        'tideglass-client-import-',
      );
      addTearDown(() => dir.deleteSync(recursive: true));
      final other = Directory.systemTemp.createTempSync(
        'tideglass-client-source-',
      );
      addTearDown(() => other.deleteSync(recursive: true));
      late String exported;
      await tester.runAsync(() async {
        final source = repository(other);
        await source.load();
        var state = const TideglassEngine()
            .advance(GameState.initial(), const Duration(seconds: 100))
            .state;
        state = const TideglassEngine().buy(state, 0, 1).state;
        await source.save(
          payload(state),
          settledThrough: DateTime.now().toUtc(),
        );
        exported = await source.exportSave();
      });
      await tester.pumpWidget(
        TideglassBootstrap(directory: dir, enableAudio: false),
      );
      await settleIo(
        tester,
        until: () => find.byType(TideglassApp).evaluate().isNotEmpty,
      );
      final before = tester.widget<TideglassApp>(find.byType(TideglassApp));
      expect(before.controller.state.counts[0], 1);
      await tester.runAsync(() => before.onImport!(exported));
      await tester.pump();
      await settleIo(
        tester,
        until: () => find.byType(TideglassApp).evaluate().isNotEmpty,
      );
      final after = tester.widget<TideglassApp>(find.byType(TideglassApp));
      expect(after.controller.state.counts[0], 2);
      expect(
        Directory('${dir.path}/recovery').listSync().whereType<File>().any(
          (f) =>
              (jsonDecode(
                        f.readAsStringSync(),
                      )['envelope']['gameplay_state']['payload']['core']['counts']
                      as List)
                  .first ==
              1,
        ),
        isTrue,
      );
      await tester.runAsync(() => after.controller.save());
      await tester.pumpWidget(const SizedBox());
      expect(tester.takeException(), isNull);
    },
  );
}
