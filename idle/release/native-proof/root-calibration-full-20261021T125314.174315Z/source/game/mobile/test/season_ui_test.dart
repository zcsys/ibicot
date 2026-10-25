import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  late DateTime now;
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  setUp(() {
    now = DateTime.utc(2026, 10, 16, 12);
  });
  GameController game({int xp = 0, StoryProgress? story}) => GameController(
    catalogue: catalogue,
    initialState: const TideglassEngine()
        .refreshContracts(
          GameState(
            daily: DailyState(passXpById: {'pass.01': BigInt.from(xp)}),
          ),
          now,
          accountSeed: 'season-ui',
          availableDiscoveryKinds: ['archive'],
        )
        .state,
    initialStory: story,
    settledThrough: story?.season == null ? null : now,
    clock: () => now,
    startTicker: false,
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
        home: SeasonScreen(game: subject, initialTab: tab),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> tap(WidgetTester tester, Finder finder) async {
    if (find.byType(SnackBar).evaluate().isNotEmpty) {
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    }
    await tester.ensureVisible(finder);
    await tester.tap(finder);
    await tester.pumpAndSettle();
  }

  testWidgets('season single and max purchases spend only event Radiance', (
    tester,
  ) async {
    final subject = game();
    addTearDown(subject.dispose);
    now = now.add(const Duration(seconds: 200));
    subject.tick();
    final main = subject.state.walletMicros;
    await show(tester, subject);
    await tap(tester, find.byKey(const ValueKey('season-buy-0')));
    expect(subject.story.season!.fleet.counts[0], 2);
    await tap(tester, find.byKey(const ValueKey('season-max-0')));
    expect(subject.story.season!.fleet.counts[0], greaterThan(2));
    expect(subject.state.walletMicros, main);
    expect(subject.state.counts, [1, 0, 0, 0, 0]);
    expect(subject.state.charts, BigInt.zero);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'free automation exposes two real policies and editable priorities at 200 percent',
    (tester) async {
      final subject = game();
      addTearDown(subject.dispose);
      await show(tester, subject, large: true);
      await tap(tester, find.byKey(const ValueKey('season-automatic')));
      expect(subject.story.season!.automatic, isTrue);
      await tap(
        tester,
        find.byKey(const ValueKey('season-policy-bestPayback')),
      );
      await tap(tester, find.text('Tier priority').last);
      expect(subject.story.season!.policy, SeasonPolicy.tierPriority);
      await tap(tester, find.byKey(const ValueKey('season-priority-up-1')));
      expect(subject.story.season!.priority, [3, 4, 2, 1, 0]);
      await tap(tester, find.text('The returning-star network'));
      expect(find.text('25%'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'archived fleet skips paused time and resumes retained progress for free',
    (tester) async {
      now = DateTime.utc(2026, 11, 14);
      final subject = game();
      addTearDown(subject.dispose);
      await show(tester, subject);
      expect(find.text('Archived fleet · paused'), findsOneWidget);
      now = now.add(const Duration(minutes: 5));
      subject.tick();
      expect(subject.story.season!.fleet.walletMicros, BigInt.zero);
      await tap(tester, find.byKey(const ValueKey('season-archive-toggle')));
      now = now.add(const Duration(minutes: 1));
      subject.tick();
      await tester.pumpAndSettle();
      expect(subject.story.season!.fleet.walletMicros, BigInt.from(60000000));
      await tap(tester, find.byKey(const ValueKey('season-archive-toggle')));
      now = now.add(const Duration(minutes: 5));
      subject.tick();
      expect(subject.story.season!.fleet.walletMicros, BigInt.from(60000000));
      expect(subject.state.surveyNotes, BigInt.zero);
    },
  );
  testWidgets('seasonal contract claim consumes the same main slot once', (
    tester,
  ) async {
    final subject = game();
    addTearDown(subject.dispose);
    final slot = subject.state.dailyContracts.first;
    await show(tester, subject, tab: 2);
    await tap(tester, find.byKey(ValueKey('bind-${slot.id}')));
    expect(subject.story.pass!.alternatives.containsKey(slot.id), isTrue);
    now = now.add(const Duration(seconds: 610));
    subject.tick();
    await tester.pumpAndSettle();
    await tap(tester, find.byKey(ValueKey('season-claim-${slot.id}')));
    expect(subject.state.surveyNotes, BigInt.from(10));
    expect(subject.state.daily.passXpById['pass.01'], BigInt.from(250));
    expect(subject.claimContract(slot.id), isFalse);
    expect(subject.claimSeasonContract(slot.id), isFalse);
    expect(subject.state.surveyNotes, BigInt.from(10));
  });
  testWidgets('main route claim also removes the seasonal claim control', (
    tester,
  ) async {
    final subject = game();
    addTearDown(subject.dispose);
    final slot = subject.state.dailyContracts.first;
    subject.bindSeasonContract(slot.id);
    now = now.add(const Duration(seconds: 610));
    subject.tick();
    if (slot.kind == 'build') {
      for (var i = 0; i < slot.target.toInt(); i++) {
        subject.buy(0);
      }
    } else if (slot.kind == 'discover') {
      subject.readArchive('archive.intro');
    }
    expect(subject.claimContract(slot.id), isTrue);
    await show(tester, subject, tab: 2, large: true);
    expect(find.byKey(ValueKey('season-claim-${slot.id}')), findsNothing);
    expect(find.byKey(ValueKey('bind-${slot.id}')), findsNothing);
    expect(subject.claimSeasonContract(slot.id), isFalse);
    expect(subject.state.daily.passXpById['pass.01'], BigInt.from(250));
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    '30 levels retain free claims and show premium without a purchase action',
    (tester) async {
      final subject = game(xp: 1500);
      addTearDown(subject.dispose);
      await show(tester, subject, tab: 1, large: true);
      expect(find.text('Level 3 / 30'), findsOneWidget);
      for (var level = 1; level <= 30; level++) {
        expect(find.byKey(PageStorageKey('level-$level')), findsOneWidget);
      }
      final reward = catalogue.seasonDefinition.reward('pass.01.free.03');
      await tap(tester, find.text('Level 3 · ${reward.title}'));
      await tap(tester, find.byKey(const ValueKey('claim-pass.01.free.03')));
      expect(subject.story.pass!.claims.containsKey(reward.id), isTrue);
      expect(subject.passEngine!.cosmeticIds(subject.story.pass!), {
        reward.contentId,
      });
      expect(subject.claimFreePassReward(reward.id), isFalse);
      expect(subject.state.daily.passXpById['pass.01'], BigInt.from(1500));
      expect(find.byKey(const ValueKey('premium-unavailable')), findsWidgets);
      expect(
        find.textContaining('Purchasing and premium delivery are unavailable'),
        findsWidgets,
      );
      expect(
        subject.story.pass!.claims.keys.any((id) => id.contains('premium')),
        isFalse,
      );
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'unlocked archive fragment becomes readable only after its real claim',
    (tester) async {
      final subject = game(xp: 500);
      addTearDown(subject.dispose);
      final reward = catalogue.seasonDefinition.reward('pass.01.free.01');
      await show(tester, subject, tab: 1);
      await tap(tester, find.text('Level 1 · ${reward.title}'));
      expect(find.text(reward.body), findsNothing);
      await tap(tester, find.byKey(ValueKey('claim-${reward.id}')));
      expect(find.text(reward.body), findsOneWidget);
      expect(subject.passEngine!.fragmentIds(subject.story.pass!), {
        reward.contentId,
      });
      expect(subject.state.walletMicros, BigInt.zero);
    },
  );
  testWidgets(
    'badge threshold claims a cosmetic receipt without an economic grant',
    (tester) async {
      final definition = catalogue.seasonDefinition;
      final initial = SeasonState.initial(
        definition,
        catalogue.seasonSchedule,
        now,
        runId: 'test-badge',
      );
      final json = initial.toJson();
      final fleet = Map<String, dynamic>.from(json['fleet']);
      fleet['lifetime_micros'] = definition.milestones.first.lifetimeMicros
          .toString();
      fleet['wallet_micros'] = fleet['lifetime_micros'];
      json['fleet'] = fleet;
      final subject = game(
        story: StoryProgress(
          season: SeasonState.fromJson(json, definition),
          pass: PassState.initial([definition]),
        ),
      );
      addTearDown(subject.dispose);
      await show(tester, subject);
      final badge = definition.milestones.first;
      await tap(tester, find.byKey(ValueKey('season-badge-${badge.id}')));
      expect(subject.story.season!.claimedMilestones, {badge.id});
      expect(subject.claimSeasonMilestone(badge.id), isFalse);
      expect(subject.state.walletMicros, BigInt.zero);
      expect(subject.state.surveyNotes, BigInt.zero);
    },
  );
  testWidgets(
    'app navigation reaches the actual local seasonal schedule without audio',
    (tester) async {
      final subject = game();
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
      await tap(tester, find.text('Logbook'));
      await tap(tester, find.byKey(const ValueKey('open-season')));
      expect(find.byType(SeasonScreen), findsOneWidget);
      expect(find.textContaining('local preview schedule'), findsOneWidget);
      expect(
        find.textContaining('16 Oct 2026 — 13 Nov 2026 UTC'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('a free reward below its XP threshold has no actionable claim', (
    tester,
  ) async {
    final subject = game(xp: 499);
    addTearDown(subject.dispose);
    await show(tester, subject, tab: 1);
    final claim = tester.widget<OutlinedButton>(
      find.byKey(const ValueKey('claim-pass.01.free.01')),
    );
    expect(claim.onPressed, isNull);
    expect(subject.claimFreePassReward('pass.01.free.01'), isFalse);
    expect(subject.story.pass!.claims, isEmpty);
  });
  testWidgets(
    'saved seasonal dates remain visible when catalogue schedule differs',
    (tester) async {
      final definition = catalogue.seasonDefinition;
      final oldRun = SeasonState.initial(
        definition,
        SeasonSchedule(DateTime.utc(2026, 9, 1)),
        now,
        runId: 'pinned-fixture',
      );
      final subject = game(
        story: StoryProgress(
          season: oldRun,
          pass: PassState.initial([definition]),
        ),
      );
      addTearDown(subject.dispose);
      await show(tester, subject, large: true);
      expect(
        find.textContaining('1 Sep 2026 — 29 Sep 2026 UTC'),
        findsOneWidget,
      );
      expect(find.text('Archived fleet · paused'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'upcoming season exposes its start without allowing early purchases',
    (tester) async {
      now = DateTime.utc(2026, 10, 15, 12);
      final subject = game();
      addTearDown(subject.dispose);
      await show(tester, subject);
      expect(find.text('Begins in 12h 0m'), findsOneWidget);
      expect(
        tester
            .widget<OutlinedButton>(find.byKey(const ValueKey('season-buy-0')))
            .onPressed,
        isNull,
      );
      expect(subject.story.season!.fleet.walletMicros, BigInt.zero);
    },
  );
}
