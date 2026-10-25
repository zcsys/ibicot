// Author staging only: run after independent contract review and lane grant.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/daily_panel.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/help_content.dart';
import 'package:tideglass/help_screen.dart';
import 'package:tideglass/number_format.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/story_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

import 'content_presentation_probe.dart';

const engine = TideglassEngine();
String two(int n) => n.toString().padLeft(2, '0');
Map<String, Object?> snapshot(GameController game) => {
  'main': game.state.toJson(),
  'story': game.story.toJson(),
};
StoryProgress prefix(int count, {DossierCollection? dossiers}) => StoryProgress(
  campaign: CampaignProgress(
    completed: List.generate(count, (i) => 'chapter.${two(i + 1)}').toSet(),
  ),
  dossiers: dossiers,
);
Finder chapterTile(int i) =>
    find.byKey(PageStorageKey('chapter-chapter.${two(i)}'));
Finder cardOf(Finder child) =>
    find.ancestor(of: child, matching: find.byType(Card)).first;

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
  tearDownAll(() {
    if (contentReportPath.isNotEmpty) {
      File(contentReportPath).writeAsStringSync(
        jsonEncode({
          'schema_version': 1,
          'kind': 'production_widget_content_observations',
          'complete': false,
          'rows': ContentProbe.rows,
          'note': 'Completeness is decided by the external checker plus unfiltered successful test log and source stability.',
        }),
      );
    }
  });
  GameController make({GameState? state, StoryProgress? story}) =>
      GameController(
        initialState: state,
        initialStory: story,
        catalogue: catalogue,
        clock: () => now,
        startTicker: false,
        settledThrough: story?.season == null ? null : now,
      );
  ContentProbe probe(WidgetTester tester) {
    final semantics = tester.ensureSemantics();
    addTearDown(semantics.dispose);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
    return ContentProbe(tester);
  }

  Future<void> story(ContentProbe p, GameController game, int tab) =>
      p.show(StoryScreen(game: game, initialTab: tab));

  for (var n = 1; n <= 6; n++) {
    testWidgets('content chapter ${two(n)} current and completed read-through', (
      tester,
    ) async {
      final p = probe(tester), chapter = catalogue.campaign.chapters[n - 1];
      final id = 'asset.chapter.${two(n)}.copy';
      for (final completed in [false, true]) {
        final game = make(story: prefix(completed ? n : n - 1));
        addTearDown(game.dispose);
        final before = snapshot(game);
        await story(p, game, 0);
        final tile = chapterTile(n);
        await p.expand('chapter-${two(n)}-header', tile, expanded: true);
        await p.read(
          'title',
          '${chapter['order']}. ${chapter['title']}',
          within: tile,
        );
        await p.read(
          'status',
          completed
              ? UiEnglish.storyRestored
              : UiEnglish.storyYourCurrentChapter,
          within: tile,
        );
        await p.read('intro', chapter['intro'] as String, within: tile);
        var i = 0;
        for (final hint in chapter['hints'] as List) {
          await p.read('hint-${i++}', '• $hint', within: tile);
        }
        var goalIndex = 0;
        for (final raw in chapter['objectives'] as List) {
          final goal = Map<String, dynamic>.from(raw),
              facts = game.progressFacts;
          String label, value;
          if (goal['kind'] == 'owned_min') {
            final tier = (goal['tier'] as int) - 1;
            label =
                UiEnglish.storyTideglassEngineProducerNamesTierInYourCurrentFleet(
                  Presentation.authored(UiEnglish.producerNames[tier]),
                );
            value = '${facts.main.counts[tier]}';
          } else if (goal['kind'] == 'challenge_family_min') {
            const families = {
              'constrained_fleets': UiEnglish.storyASmallerFleet,
              'synergy_priorities': UiEnglish.storyDifferentConnections,
              'automation_planning': UiEnglish.storyPlansForTheTide,
            };
            label = UiEnglish.storyPassagesFamilyLabelsGoalFamily(
              families[goal['family']],
            );
            value =
                '${facts.completedChallenges.where((id) => catalogue.campaign.families[id] == goal['family']).length}';
          } else {
            label = switch (goal['stat']) {
              'recharts' => UiEnglish.storyRechartsCompleted,
              'charts_awarded' => UiEnglish.storyPermanentCharts,
              'surveys_collected' => UiEnglish.storySurveysCollected,
              _ => UiEnglish.storyDistinctCalibrationPatterns,
            };
            value = switch (goal['stat']) {
              'recharts' => '${facts.recharts}',
              'charts_awarded' => '${facts.main.charts}',
              'surveys_collected' => '${facts.surveysCollected}',
              _ => '${facts.calibrations.length}',
            };
          }
          await p.read(
            'objective-${goalIndex++}',
            completed
                ? UiEnglish.storyLabelTargetAchieved(label, goal['value'])
                : '$label · $value / ${goal['value']}',
            within: tile,
          );
        }
        if (completed) {
          await p.read(
            'completion',
            chapter['completion'] as String,
            within: tile,
          );
        } else {
          expect(
            find.descendant(
              of: tile,
              matching: named(chapter['completion'] as String),
            ),
            findsNothing,
          );
        }
        await p.read(
          'keepsake',
          UiEnglish.storyKeepsakeARestoredSkyThreeArchiveEntries,
          within: tile,
        );
        expect(snapshot(game), before);
        p.row(
          id,
          completed ? 'completed' : 'current',
          'StoryScreen/chapters',
          'Seeded persisted completed prefix ${completed ? n : n - 1}; no campaign completion claim is simulated.',
          {
            'prefix_exact':
                game.story.campaign.restoredHarbor == (completed ? n : n - 1),
            'read_only': true,
            'completion_visibility': true,
            'actual_header_control': true,
          },
          before: before,
          after: snapshot(game),
        );
      }
    });
  }
  testWidgets('content locked chapter statuses retain entry boundaries', (
    tester,
  ) async {
    final p = probe(tester), game = make();
    addTearDown(game.dispose);
    await story(p, game, 0);
    for (var n = 2; n <= 6; n++) {
      final before = snapshot(game),
          c = catalogue.campaign.chapters[n - 1],
          tile = chapterTile(n);
      await p.read('title', '${c['order']}. ${c['title']}', within: tile);
      await p.read(
        'status',
        UiEnglish.storyCompleteChapterIndexFirst(n - 1),
        within: tile,
      );
      expect(game.story.campaign.completed.contains(c['id']), isFalse);
      expect(snapshot(game), before);
      p.row(
        'asset.chapter.${two(n)}.copy',
        'locked',
        'StoryScreen/chapters',
        'Seeded empty campaign.',
        {'entry_status': true, 'read_only': true},
        before: before,
        after: snapshot(game),
      );
    }
  });
  testWidgets('content ending read-through and actual return action', (
    tester,
  ) async {
    final p = probe(tester), game = make(story: prefix(6));
    addTearDown(game.dispose);
    final before = snapshot(game);
    await p.show(StoryScreen(game: game), pushed: true);
    final card = cardOf(keyed('campaign-ending'));
    await p.read('title', UiEnglish.storyTheHarborRemembers, within: card);
    await p.read(
      'text',
      catalogue.campaign.chapters.last['completion'] as String,
      within: card,
    );
    await p.checkControl(
      'ending-keep-charting',
      find.descendant(of: card, matching: find.byType(FilledButton)),
      tap: true,
    );
    expect(find.text('QA route origin'), findsOneWidget);
    expect(snapshot(game), before);
    p.row(
      'asset.ending.main',
      'ending',
      'StoryScreen/chapters',
      'Seeded six completed chapters; actual route pop.',
      {
        'ending_unlocked': game.story.campaign.hasEnding,
        'returned_to_origin': true,
        'read_only': true,
      },
      before: before,
      after: snapshot(game),
    );
  });

  for (var n = 1; n <= 18; n++) {
    testWidgets('content main archive ${two(n)} locked then reflection', (
      tester,
    ) async {
      final p = probe(tester),
          entry = catalogue.archive[n - 1],
          id = 'archive.main.${two(n)}';
      final locked = make();
      addTearDown(locked.dispose);
      await story(p, locked, 2);
      var before = snapshot(locked);
      await p.read('title', entry['title'] as String);
      expect(keyed('read-$id'), findsNothing);
      expect(named(entry['text'] as String), findsNothing);
      expect(snapshot(locked), before);
      p.row(
        'asset.$id',
        'locked',
        'StoryScreen/archive',
        'Seeded empty campaign.',
        {
          'body_hidden': true,
          'reflection_unavailable': true,
          'read_only': true,
        },
        before: before,
        after: snapshot(locked),
      );
      final game = make(story: prefix(6));
      addTearDown(game.dispose);
      await story(p, game, 2);
      final tile = find.byKey(PageStorageKey(id));
      await p.expand('$id-header', tile, expanded: true);
      await p.read('title', entry['title'] as String, within: tile);
      await p.read('text', entry['text'] as String, within: tile);
      before = snapshot(game);
      final sequence = game.state.nextDiscoverySequence;
      final notes = game.state.surveyNotes,
          xp = game.state.passXp,
          wallet = game.state.walletMicros;
      await p.checkControl('read-$id', keyed('read-$id'), tap: true);
      expect(game.story.campaign.archiveIds, contains(id));
      expect(game.state.daily.discoveryTotals['archive'], BigInt.one);
      expect(game.state.nextDiscoverySequence, sequence + BigInt.one);
      expect(game.state.surveyNotes, notes);
      expect(game.state.passXp, xp);
      expect(game.state.walletMicros, wallet);
      p.row(
        'asset.$id',
        'reflected',
        'StoryScreen/archive',
        'Seeded restored campaign; actual reflection callback.',
        {
          'discovery_once': true,
          'actual_reflection_control': true,
          'no_direct_notes_xp_or_radiance': true,
        },
        before: before,
        after: snapshot(game),
      );
    });
  }

  for (var n = 1; n <= 12; n++) {
    testWidgets('content dossier ${two(n)} introduction and final scene', (
      tester,
    ) async {
      final p = probe(tester),
          definition = catalogue.dossiers[n - 1],
          id = definition.id;
      final game = make(
        state: GameState(surveyNotes: BigInt.from(150)),
        story: prefix(3),
      );
      addTearDown(game.dispose);
      await story(p, game, 1);
      final card = cardOf(keyed('open-$id'));
      await p.read('title', definition.title, within: card);
      await p.read('intro', definition.intro, within: card);
      final before = snapshot(game),
          wallet = game.state.walletMicros,
          charts = game.state.charts;
      await p.checkControl('open-$id', keyed('open-$id'), tap: true);
      final dialog = find.byType(Dialog);
      expect(game.state.surveyNotes, BigInt.from(150));
      await p.checkControl(
        'confirm-$id',
        find.descendant(of: dialog, matching: find.byType(FilledButton)),
        tap: true,
      );
      expect(game.state.surveyNotes, BigInt.from(50));
      expect(game.story.dossiers.owned, {id});
      expect(game.story.dossiers.active!.dossierId, id);
      expect(game.state.walletMicros, wallet);
      expect(game.state.charts, charts);
      p.row(
        'asset.$id.copy',
        'opened',
        'StoryScreen/passages',
        'Seeded chapter 3 and 150 Notes; actual confirmation spends 100.',
        {
          'confirmation_before_spend': true,
          'exact_100_notes': true,
          'actual_dossier_identity': true,
          'main_power_unchanged': true,
        },
        before: before,
        after: snapshot(game),
      );
      final finalGame = make(
        story: prefix(
          3,
          dossiers: DossierCollection(
            owned: {id},
            completed: {id},
            active: ChallengeRun(
              dossierId: id,
              fleet: GameState(
                walletMicros: definition.goalMicros,
                lifetimeMicros: definition.goalMicros,
              ),
              complete: true,
            ),
          ),
        ),
      );
      addTearDown(finalGame.dispose);
      await story(p, finalGame, 1);
      final finalBefore = snapshot(finalGame),
          active = keyed('active-challenge');
      await p.read('title', definition.title, within: active);
      await p.read('completion', definition.completion, within: active);
      await p.read(
        'status',
        UiEnglish.storyPassageChartedItsDiscoveryIsKeptIn,
        within: active,
      );
      expect(finalGame.story.dossiers.active!.complete, isTrue);
      expect(finalGame.story.dossiers.completed, {id});
      expect(snapshot(finalGame), finalBefore);
      p.row(
        'asset.$id.copy',
        'completed',
        'StoryScreen/passages',
        'Seeded valid final scenario goal; presentation only, not a simulated completion route.',
        {
          'actual_final_scene_identity': true,
          'goal_met': true,
          'read_only': true,
        },
        before: finalBefore,
        after: snapshot(finalGame),
      );
    });
  }

  for (var n = 1; n <= 20; n++) {
    testWidgets('content seasonal fragment ${two(n)} locked and actual claim', (
      tester,
    ) async {
      final p = probe(tester), id = 'archive.season01.${two(n)}';
      final reward = catalogue.seasonDefinition.rewards.singleWhere(
        (r) => r.contentId == id,
      );
      for (final ready in [false, true]) {
        final game = make(
          state: GameState(
            daily: DailyState(
              passXpById: {'pass.01': BigInt.from(ready ? 15000 : 0)},
            ),
          ),
        );
        addTearDown(game.dispose);
        await p.show(SeasonScreen(game: game, initialTab: 1));
        final tile = find.byKey(PageStorageKey('level-${reward.level}'));
        await p.expand('level-${reward.level}', tile, expanded: true);
        await p.read(
          'title',
          UiEnglish.seasonLevelValueFreeTitle(
            reward.level,
            Presentation.authored(reward.title),
          ),
          within: tile,
        );
        expect(keyed('reward-copy-${reward.id}'), findsNothing);
        await p.read(
          'locked-placeholder',
          UiEnglish.seasonCollectThisAccountAtLevelValueTo(reward.level),
          within: tile,
        );
        final before = snapshot(game), mainBefore = game.state.toJson();
        if (!ready) {
          await p.checkControl(
            'claim-${reward.id}',
            keyed('claim-${reward.id}'),
            enabled: false,
          );
          expect(game.story.pass!.claims.containsKey(reward.id), isFalse);
          expect(snapshot(game), before);
          p.row(
            'asset.$id',
            'locked',
            'SeasonScreen/pass',
            'Seeded zero XP, no ownership.',
            {'body_hidden': true, 'claim_disabled': true, 'read_only': true},
            before: before,
            after: snapshot(game),
          );
        } else {
          await p.checkControl(
            'claim-${reward.id}',
            keyed('claim-${reward.id}'),
            tap: true,
          );
          await p.read('body', reward.body, within: tile);
          expect(game.passEngine!.fragmentIds(game.story.pass!), {id});
          expect(game.story.pass!.claims.keys.toSet(), {reward.id});
          expect(game.claimFreePassReward(reward.id), isFalse);
          expect(game.state.toJson(), mainBefore);
          await p.checkControl(
            'claimed-${reward.id}',
            keyed('claim-${reward.id}'),
            enabled: false,
          );
          p.row(
            'asset.$id',
            'claimed',
            'SeasonScreen/pass',
            'Seeded 15000 earned XP; actual free claim, no premium authority.',
            {
              'actual_fragment_identity': true,
              'one_claim_only': true,
              'main_ledger_unchanged': true,
              'claimed_control_disabled': true,
            },
            before: before,
            after: snapshot(game),
          );
        }
      }
    });
  }

  for (final phase in ['upcoming', 'live', 'archived']) {
    testWidgets('content season $phase and archive activity', (tester) async {
      final p = probe(tester), schedule = catalogue.seasonSchedule;
      now = DateTime.fromMicrosecondsSinceEpoch(
        (phase == 'upcoming'
                ? schedule.startsAtMicros - BigInt.one
                : phase == 'live'
                ? schedule.startsAtMicros + BigInt.one
                : schedule.endsAtMicros)
            .toInt(),
        isUtc: true,
      );
      final game = make();
      addTearDown(game.dispose);
      await p.show(SeasonScreen(game: game));
      final before = snapshot(game);
      await p.read('title', catalogue.seasonDefinition.title);
      await p.read('phase-copy', catalogue.seasonDefinition.copy[phase]!);
      expect(game.story.season!.phase.name, phase);
      if (phase == 'archived') {
        await p.read('ended', catalogue.seasonDefinition.copy['ended']!);
        await p.read(
          'archive_resume',
          catalogue.seasonDefinition.copy['archive_resume']!,
        );
        await p.checkControl('archive-resume', keyed('season-archive-toggle'));
      }
      expect(snapshot(game), before);
      p.row(
        'asset.season.01.copy',
        phase == 'archived' ? 'archived-paused' : phase,
        'SeasonScreen/fleet',
        'Fresh season at exact schedule boundary.',
        {'phase_exact': true, 'read_only': true},
        before: before,
        after: snapshot(game),
      );
      if (phase == 'archived') {
        final wallet = game.story.season!.fleet.walletMicros,
            main = game.state.toJson();
        await p.checkControl(
          'archive-resume',
          keyed('season-archive-toggle'),
          tap: true,
        );
        await p.read(
          'phase-copy',
          catalogue.seasonDefinition.copy['archived']!,
        );
        expect(game.story.season!.archiveActive, isTrue);
        expect(game.story.season!.fleet.walletMicros, wallet);
        expect(game.state.toJson(), main);
        await p.checkControl(
          'archive-pause',
          keyed('season-archive-toggle'),
          tap: true,
        );
        expect(game.story.season!.archiveActive, isFalse);
        expect(game.story.season!.fleet.walletMicros, wallet);
        expect(game.state.toJson(), main);
        p.row(
          'asset.season.01.copy',
          'archive-resume-pause',
          'SeasonScreen/fleet',
          'Actual archive toggle callbacks at fixed clock.',
          {
            'resume_then_pause': true,
            'no_money_or_xp_grant': true,
            'retained_wallet': true,
          },
          before: before,
          after: snapshot(game),
        );
      }
    });
  }
  testWidgets('content season pass and alternative explanatory copy', (
    tester,
  ) async {
    final p = probe(tester), game = make();
    addTearDown(game.dispose);
    for (final tab in [1, 2]) {
      await p.show(SeasonScreen(game: game, initialTab: tab));
      final before = snapshot(game);
      await p.read('title', catalogue.seasonDefinition.title);
      await p.read(
        tab == 1 ? 'pass' : 'alternative',
        catalogue.seasonDefinition.copy[tab == 1 ? 'pass' : 'alternative']!,
      );
      expect(snapshot(game), before);
      p.row(
        'asset.season.01.copy',
        tab == 1 ? 'pass' : 'alternatives',
        'SeasonScreen/${tab == 1 ? 'pass' : 'contracts'}',
        'Fresh season; existing economic alternative tests remain separate.',
        {'read_only': true, 'actual_route_copy': true},
        before: before,
        after: snapshot(game),
      );
    }
  });

  final helpAssets = {
    HelpTopic.play: 'asset.support.help',
    HelpTopic.rechart: 'asset.support.help',
    HelpTopic.away: 'asset.support.help',
    HelpTopic.notes: 'asset.support.help',
    HelpTopic.recovery: 'asset.support.recovery_guide',
    HelpTopic.credits: 'asset.support.credits',
    HelpTopic.releaseNotes: 'asset.support.release_notes',
    HelpTopic.privacy: 'flow.help.privacy-companion',
  };
  for (final topic in HelpTopic.values) {
    testWidgets('content help ${topic.name} full article and callbacks', (
      tester,
    ) async {
      final p = probe(tester), game = make();
      addTearDown(game.dispose);
      final before = snapshot(game),
          article = HelpContent.article(topic),
          calls = <String>[];
      await p.show(
        HelpScreen(
          onOpenAccount: () => calls.add('account'),
          onOpenLocalRecovery: () => calls.add('localRecovery'),
          onOpenPrivacySettings: () => calls.add('privacySettings'),
        ),
      );
      await p.read('index-title', HelpCopy.title);
      await p.read('index-intro', HelpCopy.intro);
      await p.read('index-summary', article.summary);
      await p.checkControl(
        'help-topic-${topic.name}',
        keyed('help-topic-${topic.name}'),
        tap: true,
      );
      await p.read('title', article.title);
      await p.read('summary', article.summary);
      for (final section in article.sections) {
        await p.read('heading-${section.id}', section.title);
        for (var i = 0; i < section.paragraphs.length; i++) {
          await p.read('${section.id}-paragraph-$i', section.paragraphs[i]);
        }
      }
      if (topic == HelpTopic.releaseNotes) {
        await p.read('development-notice', HelpCopy.developmentNotice);
      }
      for (final action in article.actions) {
        await p.checkControl(
          'help-action-${action.name}',
          keyed('help-action-${action.name}'),
          tap: true,
        );
        if (action == HelpAction.licenses) {
          expect(find.byType(LicensePage), findsOneWidget);
          await p.checkControl(
            'licenses-back',
            find.byType(BackButton),
            tap: true,
          );
        } else {
          expect(calls.last, action.name);
        }
      }
      await p.checkControl(
        'help-all-topics',
        keyed('help-all-topics'),
        tap: true,
      );
      expect(keyed('help-scroll-index'), findsOneWidget);
      expect(snapshot(game), before);
      p.row(
        helpAssets[topic]!,
        topic.name,
        'HelpScreen/${topic.name}',
        'Actual index → article → index navigation; injected host callback spies, no network.',
        {
          'all_sections_read': true,
          'actual_navigation': true,
          'callbacks_forwarded': true,
          'game_unchanged': true,
        },
        before: before,
        after: snapshot(game),
      );
    });
  }

  GameState contracts({required bool backlog, required bool ready}) {
    var state = engine
        .refreshContracts(
          GameState.initial(),
          backlog ? now.subtract(const Duration(days: 6)) : now,
          accountSeed: 'content-proof',
          availableDiscoveryKinds: ['archive'],
        )
        .state;
    if (backlog) {
      state = engine
          .refreshContracts(state, now, availableDiscoveryKinds: ['archive'])
          .state;
    }
    if (ready) {
      var lifetime = state.lifetimeMicros,
          purchased = state.lifetimePurchasedCount;
      final totals = Map<String, BigInt>.from(state.daily.discoveryTotals);
      for (final c in state.dailyContracts) {
        if (c.kind == 'restore' &&
            c.lifetimeBaselineMicros + c.target > lifetime) {
          lifetime = c.lifetimeBaselineMicros + c.target;
        }
        if (c.kind == 'build' && c.purchasedBaseline + c.target > purchased) {
          purchased = c.purchasedBaseline + c.target;
        }
        if (c.kind == 'discover') {
          totals[c.discoveryKind!] = c.discoveryBaseline + c.target;
        }
      }
      state = state.copyWith(
        lifetimeMicros: lifetime,
        lifetimePurchasedCount: purchased,
        daily: state.daily.copyWith(discoveryTotals: totals),
      );
    }
    return state;
  }

  Future<void> panel(ContentProbe p, GameController game) => p.show(
    Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ListenableBuilder(
            listenable: game,
            builder: (_, _) => ContractPanel(game: game),
          ),
        ),
      ),
    ),
  );
  Future<void> panelText(ContentProbe p, GameController game) async {
    await p.read('title', UiEnglish.dailyCrewContracts);
    await p.read('retention', UiEnglish.dailyThreeEachAccountDayKeptForSeven);
    await p.read(
      'status',
      UiEnglish.dailyGameStateDailyContractsWhereCCClaimed(
        game.state.dailyContracts.where((c) => c.claimed).length,
        game.state.passXp,
      ),
    );
    await p.read(
      'account-day',
      UiEnglish.dailyAccountDayUsesAFixedUTCGame(
        game.state.daily.utcOffsetMinutes >= 0 ? '+' : '',
        game.state.daily.utcOffsetMinutes / 60,
      ),
    );
  }

  Future<void> contractText(
    ContentProbe p,
    GameController game,
    DailyContract c,
  ) async {
    final card = cardOf(keyed('claim-${c.id}'));
    final title = switch (c.kind) {
      'restore' => UiEnglish.dailyGatherCompactMicrosContractTargetRadiance(
        compactMicros(c.target),
      ),
      'build' => UiEnglish.dailyBuildContractTargetLightkeepers(c.target),
      _ =>
        UiEnglish.dailyExploreOneSwitchContractDiscoveryKindCalibrationConstellation(
          switch (c.discoveryKind) {
            'calibration' => UiEnglish.constellationNoun,
            'challenge' => UiEnglish.challengeNoun,
            _ => UiEnglish.dailyArchiveEntry,
          },
        ),
    };
    final progress = game.engine.contractProgress(game.state, c),
        age = game.state.daily.dayHighWater - c.accountDay;
    final shown = c.kind == 'restore'
        ? UiEnglish.dailyCompactMicrosProgressCompactMicrosContractTargetR(
            compactMicros(progress),
            compactMicros(c.target),
          )
        : '$progress / ${c.target}';
    await p.read(
      'contract-${c.slot}-${c.accountDay}-title',
      title,
      within: card,
    );
    await p.read(
      'contract-${c.slot}-${c.accountDay}-progress',
      '$shown · ${age == 0 ? UiEnglish.dailyToday : UiEnglish.dailyAgeDInTheBacklog(age)}',
      within: card,
    );
  }

  testWidgets('content daily pending reroll and status', (tester) async {
    final p = probe(tester),
        game = make(state: contracts(backlog: false, ready: false));
    addTearDown(game.dispose);
    await panel(p, game);
    final before = snapshot(game);
    await panelText(p, game);
    for (final c in game.state.dailyContracts) {
      await contractText(p, game, c);
      await p.checkControl(
        'claim-${c.id}',
        keyed('claim-${c.id}'),
        enabled: false,
      );
    }
    final c = game.state.dailyContracts.first,
        card = cardOf(keyed('claim-${c.id}'));
    await p.checkControl(
      'reroll-${c.id}',
      find.descendant(of: card, matching: find.byType(TextButton)),
      tap: true,
    );
    final replacement = game.state.dailyContracts.singleWhere(
      (v) => v.id == c.id,
    );
    expect(replacement.rerolled, isTrue);
    expect(game.rerollContract(c.id), isFalse);
    expect(
      find.descendant(
        of: cardOf(keyed('claim-${c.id}')),
        matching: find.byType(TextButton),
      ),
      findsNothing,
    );
    await contractText(p, game, replacement);
    expect(game.state.surveyNotes, BigInt.zero);
    expect(game.state.passXp, BigInt.zero);
    p.row(
      'flow.daily.contracts',
      'pending-reroll',
      'ContractPanel',
      'Production daily generator; one actual reroll callback.',
      {
        'three_pending': game.state.dailyContracts.length == 3,
        'reroll_once': true,
        'no_reward': true,
      },
      before: before,
      after: snapshot(game),
    );
  });
  testWidgets('content daily ready backlog claims and empty state', (
    tester,
  ) async {
    final p = probe(tester),
        game = make(state: contracts(backlog: true, ready: true));
    addTearDown(game.dispose);
    await panel(p, game);
    final before = snapshot(game);
    await panelText(p, game);
    expect(game.state.dailyContracts.length, 21);
    final readyContracts = List<DailyContract>.from(game.state.dailyContracts);
    for (final c in readyContracts) {
      await contractText(p, game, c);
      expect(
        game.engine.contractProgress(game.state, c),
        greaterThanOrEqualTo(c.target),
      );
      await p.checkControl('claim-${c.id}', keyed('claim-${c.id}'), tap: true);
      expect(game.claimContract(c.id), isFalse);
      expect(keyed('claim-${c.id}'), findsNothing);
    }
    expect(game.state.surveyNotes, BigInt.from(210));
    expect(game.state.passXp, BigInt.from(5250));
    p.row(
      'flow.daily.contracts',
      'ready-backlog',
      'ContractPanel',
      'Production generator for seven days; exact goal progress seeded, actual 21 claims.',
      {
        'seven_days_21_slots': true,
        'exact_210_notes_5250_xp': true,
        'claims_once': true,
      },
      before: before,
      after: snapshot(game),
    );
    final emptyBefore = snapshot(game);
    await panelText(p, game);
    await p.read(
      'empty',
      UiEnglish.dailyAllRetainedContractsAreCompleteTheHarbor,
    );
    expect(find.byType(FilledButton), findsNothing);
    expect(snapshot(game), emptyBefore);
    p.row(
      'flow.daily.contracts',
      'empty',
      'ContractPanel',
      'Reached by actual claims, not hand-authored claimed flags.',
      {
        'all_21_claimed': game.state.dailyContracts.every((c) => c.claimed),
        'no_claim_controls': true,
        'read_only': true,
      },
      before: emptyBefore,
      after: snapshot(game),
    );
  });
  testWidgets(
    'content daily timers queued ready and emptied by actual collection',
    (tester) async {
      final p = probe(tester),
          game = make(
            state: GameState(
              focusCharges: 10,
              focusRemainingMicros: BigInt.from(1200000000),
              completedSurveys: 3,
            ),
          );
      addTearDown(game.dispose);
      await p.show(
        TideglassApp(
          controller: game,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
        ),
        app: true,
      );
      await p.checkControl(
        'journal',
        find.byType(NavigationDestination).at(2),
        tap: true,
      );
      final before = snapshot(game);
      await p.read('daily-title', UiCopy.theHarborSRhythm);
      await p.read('focus-label', UiCopy.focusStored);
      await p.read('focus-store', '10 / 12');
      await p.read('focus-help', UiCopy.oneChargeEveryTwoHoursEach);
      await p.read(
        'focus-queued',
        UiEnglish.appFocusedForDurationLabelDurationMicrosecondsGameState(
          durationLabel(const Duration(minutes: 20)),
        ),
      );
      await p.read('survey-label', UiCopy.surveysComplete);
      await p.read('survey-store', '3 / 3');
      await p.read('survey-help', UiCopy.oneSurveyEveryEightHoursUp);
      await p.checkControl('focus-route', keyed('activate-focus'));
      await p.checkControl(
        'collect-surveys',
        keyed('collect-surveys'),
        tap: true,
      );
      expect(game.state.completedSurveys, 0);
      expect(game.state.surveyNotes, BigInt.from(30));
      expect(game.state.focusCharges, 10);
      expect(game.state.focusRemainingMicros, BigInt.from(1200000000));
      p.row(
        'flow.daily.storage',
        'queued-ready',
        'TideglassApp/journal',
        'Seeded valid stored Focus/queue and three Surveys; actual collect callback.',
        {
          'exact_30_notes': true,
          'focus_queue_unchanged': true,
          'storage_consumed': true,
        },
        before: before,
        after: snapshot(game),
      );
      final emptyBefore = snapshot(game);
      await p.read('survey-store', '0 / 3');
      await p.checkControl(
        'collect-empty',
        keyed('collect-surveys'),
        enabled: false,
      );
      expect(snapshot(game), emptyBefore);
      p.row(
        'flow.daily.storage',
        'empty',
        'TideglassApp/journal',
        'Actual collection result.',
        {'disabled_when_empty': true, 'read_only': true},
        before: emptyBefore,
        after: snapshot(game),
      );
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}
