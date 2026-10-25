import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/harbor_art.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/story_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final now = DateTime.utc(2026, 10, 16);
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  GameController game({GameState? main, StoryProgress? story}) =>
      GameController(
        initialState: main,
        initialStory: story,
        catalogue: catalogue,
        clock: () => now,
        startTicker: false,
      );
  StoryProgress chapters(int count, {DossierCollection? dossiers}) =>
      StoryProgress(
        campaign: CampaignProgress(
          completed: List.generate(
            count,
            (i) => 'chapter.${(i + 1).toString().padLeft(2, '0')}',
          ).toSet(),
        ),
        dossiers: dossiers,
      );
  Future<void> show(
    WidgetTester tester,
    GameController subject, {
    int tab = 0,
    bool large = false,
  }) async {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: tideglassTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context).copyWith(
            disableAnimations: true,
            textScaler: TextScaler.linear(large ? 2 : 1),
          ),
          child: child!,
        ),
        home: StoryScreen(game: subject, initialTab: tab),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets(
    'six actual chapters show first unmet goal and retained progress',
    (tester) async {
      final subject = game();
      addTearDown(subject.dispose);
      await show(tester, subject);
      expect(find.text('0 of 6 constellations restored'), findsOneWidget);
      expect(find.text('Recharts completed · 0 / 1'), findsOneWidget);
      for (final chapter in catalogue.campaign.chapters) {
        expect(
          find.text('${chapter['order']}. ${chapter['title']}'),
          findsOneWidget,
        );
      }
      expect(find.byKey(const ValueKey('campaign-ending')), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'new dossier charge confirms once, main Radiance remains separate',
    (tester) async {
      final main = GameState(
        walletMicros: BigInt.from(500000000),
        lifetimeMicros: BigInt.from(500000000),
        surveyNotes: BigInt.from(150),
      );
      final subject = game(main: main, story: chapters(3));
      addTearDown(subject.dispose);
      await show(tester, subject, tab: 1);
      final first = find.byKey(const ValueKey('open-challenge.01'));
      await tester.ensureVisible(first);
      await tester.tap(first);
      await tester.pumpAndSettle();
      expect(subject.state.surveyNotes, BigInt.from(150));
      await tester.tap(find.widgetWithText(FilledButton, 'Open dossier'));
      await tester.pumpAndSettle();
      expect(subject.state.surveyNotes, BigInt.from(50));
      expect(subject.state.walletMicros, main.walletMicros);
      expect(subject.story.dossiers.owned, {'challenge.01'});
      expect(subject.story.dossiers.active!.fleet.walletMicros, BigInt.zero);
      expect(find.byKey(const ValueKey('active-challenge')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('replacement cancellation keeps current passage and Notes', (
    tester,
  ) async {
    final collection = DossierCollection(
      owned: {'challenge.01'},
      active: ChallengeEconomy(catalogue.dossiers.first).newRun(),
    );
    final subject = game(
      main: GameState(surveyNotes: BigInt.from(200)),
      story: chapters(3, dossiers: collection),
    );
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 1);
    final second = find.byKey(const ValueKey('open-challenge.02'));
    await tester.ensureVisible(second);
    await tester.tap(second);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Keep current progress'));
    await tester.pumpAndSettle();
    expect(subject.story.dossiers.active!.dossierId, 'challenge.01');
    expect(subject.state.surveyNotes, BigInt.from(200));
  });
  testWidgets('manual passage purchase changes only the passage fleet', (
    tester,
  ) async {
    final definition = catalogue.dossiers.first;
    final fleet = const TideglassEngine()
        .advance(GameState.initial(), const Duration(seconds: 100))
        .state;
    final run = ChallengeRun(dossierId: definition.id, fleet: fleet);
    final subject = game(
      main: GameState(surveyNotes: BigInt.from(25)),
      story: chapters(
        3,
        dossiers: DossierCollection(owned: {definition.id}, active: run),
      ),
    );
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 1);
    final before = subject.state.walletMicros;
    final purchase = find.byKey(const ValueKey('challenge-buy-0'));
    await tester.ensureVisible(purchase);
    await tester.tap(purchase);
    await tester.pumpAndSettle();
    expect(subject.story.dossiers.active!.fleet.counts[0], 2);
    expect(subject.state.counts[0], 1);
    expect(subject.state.walletMicros, before);
    expect(subject.state.surveyNotes, BigInt.from(25));
  });
  testWidgets('crew priority reordering persists actual alternative policy', (
    tester,
  ) async {
    final definition = catalogue.dossiers[8];
    final run = ChallengeEconomy(
      definition,
    ).newRun().copyWith(policy: ChallengePolicy.tierPriority);
    final subject = game(
      story: chapters(
        3,
        dossiers: DossierCollection(owned: {definition.id}, active: run),
      ),
    );
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 1, large: true);
    final up = find.byKey(const ValueKey('priority-up-1'));
    await tester.ensureVisible(up);
    await tester.tap(up);
    await tester.pumpAndSettle();
    expect(subject.story.dossiers.active!.priority, [3, 4, 2, 1, 0]);
    expect(subject.story.dossiers.active!.automatic, isTrue);
    expect(tester.takeException(), isNull);
  });
  testWidgets('only restored archive entries permit actual reflection', (
    tester,
  ) async {
    final subject = game(story: chapters(1));
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 2);
    expect(find.text('3 of 18 accounts recovered'), findsOneWidget);
    await tester.tap(find.text('The First Skiff'));
    await tester.pumpAndSettle();
    final read = find.byKey(const ValueKey('read-archive.main.01'));
    await tester.ensureVisible(read);
    await tester.tap(read);
    await tester.pump();
    expect(
      subject.lastAction,
      'The keeper’s account is recorded in your logbook.',
    );
    expect(find.byKey(const ValueKey('read-archive.main.04')), findsNothing);
  });
  testWidgets('six permanent chapters reveal the authored ending', (
    tester,
  ) async {
    final subject = game(story: chapters(6));
    addTearDown(subject.dispose);
    await show(tester, subject, large: true);
    expect(find.byKey(const ValueKey('campaign-ending')), findsOneWidget);
    expect(
      find.text(catalogue.campaign.chapters.last['completion'] as String),
      findsWidgets,
    );
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'decoration purchase equips visible art and changes no production',
    (tester) async {
      final subject = game(main: GameState(surveyNotes: BigInt.from(50)));
      addTearDown(subject.dispose);
      await show(tester, subject, tab: 3);
      final before = subject.engine.outputPerSecond(subject.state).raw;
      final purchase = find.byKey(const ValueKey('decoration-1'));
      await tester.ensureVisible(purchase);
      await tester.tap(purchase);
      await tester.pumpAndSettle();
      expect(subject.story.equippedDecoration, 'cosmetic.core.decoration.01');
      expect(subject.state.surveyNotes, BigInt.zero);
      expect(subject.engine.outputPerSecond(subject.state).raw, before);
      expect(
        tester.widget<HarborArt>(find.byType(HarborArt).first).decoration,
        'cosmetic.core.decoration.01',
      );
    },
  );
  testWidgets('app reaches restoration and binds permanent harbor state', (
    tester,
  ) async {
    final subject = game(story: chapters(2));
    addTearDown(subject.dispose);
    await tester.pumpWidget(
      TideglassApp(
        controller: subject,
        initialPreferences: const ClientPreferences(
          reduceMotion: true,
          onboardingDismissed: true,
        ),
      ),
    );
    await tester.pump();
    expect(tester.widget<HarborArt>(find.byType(HarborArt)).restoration, 2);
    await tester.tap(find.text('Logbook'));
    await tester.pumpAndSettle();
    final open = find.byKey(const ValueKey('open-story'));
    await tester.ensureVisible(open);
    await tester.tap(open);
    await tester.pumpAndSettle();
    expect(find.text('2 of 6 constellations restored'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('restart and owned replay are explicit and never charge twice', (
    tester,
  ) async {
    final definition = catalogue.dossiers.first;
    final fleet = const TideglassEngine()
        .advance(GameState.initial(), const Duration(seconds: 100))
        .state;
    final subject = game(
      main: GameState(surveyNotes: BigInt.from(25)),
      story: chapters(
        3,
        dossiers: DossierCollection(
          owned: {definition.id},
          active: ChallengeRun(dossierId: definition.id, fleet: fleet),
        ),
      ),
    );
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 1);
    final restart = find.text('Restart fleet · free');
    await tester.ensureVisible(restart);
    await tester.tap(restart);
    await tester.pumpAndSettle();
    expect(
      subject.story.dossiers.active!.fleet.walletMicros,
      fleet.walletMicros,
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Restart fleet'));
    await tester.pumpAndSettle();
    expect(subject.story.dossiers.active!.fleet.walletMicros, BigInt.zero);
    expect(subject.state.surveyNotes, BigInt.from(25));
    final close = find.text('Close this passage');
    await tester.ensureVisible(close);
    await tester.tap(close);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Close passage'));
    await tester.pumpAndSettle();
    expect(subject.story.dossiers.active, isNull);
    final reopen = find.byKey(ValueKey('open-${definition.id}'));
    await tester.ensureVisible(reopen);
    await tester.tap(reopen);
    await tester.pumpAndSettle();
    expect(find.textContaining('Opening it is free.'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Open dossier'));
    await tester.pumpAndSettle();
    expect(subject.story.dossiers.active!.dossierId, definition.id);
    expect(subject.state.surveyNotes, BigInt.from(25));
  });
  testWidgets('decorations can be removed while ownership is retained', (
    tester,
  ) async {
    const id = 'cosmetic.core.decoration.02';
    final subject = game(
      story: StoryProgress(decorations: {id}, equippedDecoration: id),
    );
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 3, large: true);
    final remove = find.byKey(const ValueKey('unequip-decoration'));
    await tester.ensureVisible(remove);
    await tester.tap(remove);
    await tester.pumpAndSettle();
    expect(subject.story.equippedDecoration, isNull);
    expect(subject.story.decorations, {id});
    expect(tester.takeException(), isNull);
  });
  testWidgets('expanded network and archive fit 320px at 200 percent text', (
    tester,
  ) async {
    final definition = catalogue.dossiers[4];
    final subject = game(
      story: chapters(
        3,
        dossiers: DossierCollection(
          owned: {definition.id},
          active: ChallengeEconomy(definition).newRun(),
        ),
      ),
    );
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 1, large: true);
    final rules = find.text('Passage network rules');
    await tester.ensureVisible(rules);
    await tester.tap(rules);
    await tester.pumpAndSettle();
    expect(find.text('Nurseries'), findsOneWidget);
    expect(tester.takeException(), isNull);
    final archive = find.byKey(const ValueKey('story-tab-2'));
    await tester.ensureVisible(archive);
    await tester.tap(archive);
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('The First Skiff'));
    await tester.tap(find.text('The First Skiff'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('read-archive.main.01')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
