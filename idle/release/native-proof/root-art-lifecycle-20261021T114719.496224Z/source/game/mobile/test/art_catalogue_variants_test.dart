import 'dart:convert';
import 'dart:io';
import 'dart:ui' show SemanticsAction, SemanticsFlag;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/cosmetic_art.dart';
import 'package:tideglass/cosmetics.dart';
import 'package:tideglass/cosmetics_screen.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/harbor_art.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/producer_art.dart';
import 'package:tideglass/producer_art_data.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

// All states here are deterministic engineering fixtures. Paid IDs supplied to
// the verifier callback are synthetic, not store/provider ownership evidence.
// No canonical asset verification, rights or native-device gate is written.
const _reportDirectory = String.fromEnvironment(
  'TIDEGLASS_ART_REPORT_DIR',
  defaultValue: '../../release/art/catalogue-variants/author-run',
);
final _clock = DateTime.utc(2026, 10, 21, 12);
final _rows = <Map<String, Object?>>[];
final _supplemental = <Map<String, Object?>>[];

class _Display {
  const _Display(this.name, this.size, this.textScale, this.reducedMotion);
  final String name;
  final Size size;
  final double textScale;
  final bool reducedMotion;
  String get id => '$name-${(textScale * 100).round()}-${reducedMotion ? 'reduced' : 'normal'}';
  Map<String, Object?> get json => {
    'condition_id': id,
    'viewport': [size.width, size.height],
    'text_scale': textScale,
    'reduced_motion': reducedMotion,
    'environment': 'Flutter host test; not a physical device',
  };
}

final _displays = [
  for (final viewport in {'phone': const Size(320, 720), 'tablet': const Size(1024, 768)}.entries)
    for (final scale in [1.0, 1.5, 2.0])
      for (final reduced in [false, true])
        _Display(viewport.key, viewport.value, scale, reduced),
];

void _configure(WidgetTester tester, _Display display) {
  tester.view.physicalSize = display.size;
  tester.view.devicePixelRatio = 1;
  tester.platformDispatcher.textScaleFactorTestValue = display.textScale;
  tester.platformDispatcher.accessibilityFeaturesTestValue =
      FakeAccessibilityFeatures(disableAnimations: display.reducedMotion);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  addTearDown(tester.platformDispatcher.clearAccessibilityFeaturesTestValue);
}

Future<void> _frames(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 20));
  expect(tester.takeException(), isNull);
}

Future<void> _disposeView(WidgetTester tester) async {
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.pump();
  expect(tester.takeException(), isNull);
  expect(tester.binding.transientCallbackCount, 0,
      reason: 'A removed presentation must not retain animation callbacks.');
}

Future<void> _showApp(WidgetTester tester, GameController game, _Display display) async {
  await tester.pumpWidget(TideglassApp(
    key: UniqueKey(),
    controller: game,
    initialPreferences: ClientPreferences(
      reduceMotion: display.reducedMotion,
      onboardingDismissed: true,
    ),
  ));
  await _frames(tester);
}

Future<void> _showScreen(WidgetTester tester, Widget child, _Display display) async {
  await tester.pumpWidget(MaterialApp(
    key: UniqueKey(),
    theme: tideglassTheme(),
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context).copyWith(
        disableAnimations: display.reducedMotion,
        textScaler: TextScaler.linear(display.textScale),
      ),
      child: child!,
    ),
    home: child,
  ));
  await _frames(tester);
}

Future<void> _reachable(WidgetTester tester, Finder finder, _Display display,
    {bool enabled = true}) async {
  await tester.ensureVisible(finder);
  await _frames(tester);
  final rect = tester.getRect(finder);
  expect(rect.width, greaterThanOrEqualTo(48), reason: 'Control width');
  expect(rect.height, greaterThanOrEqualTo(48), reason: 'Control height');
  expect(rect.left, greaterThanOrEqualTo(-.5));
  expect(rect.right, lessThanOrEqualTo(display.size.width + .5));
  expect(rect.top, greaterThanOrEqualTo(-.5));
  expect(rect.bottom, lessThanOrEqualTo(display.size.height + .5));
  expect(finder.hitTestable(), findsOneWidget);
  final semantics = tester.getSemantics(finder).getSemanticsData();
  expect(semantics.hasFlag(SemanticsFlag.isButton), isTrue);
  expect(semantics.label.trim(), isNotEmpty);
  expect(semantics.hasAction(SemanticsAction.tap), enabled);
}

void _row(String assetId, String group, _Display display, Map<String, Object?> evidence) {
  _rows.add({'asset_id': assetId, 'group': group, ...display.json, 'result': 'passed_bounded_host_case', ...evidence});
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  setUpAll(() async { catalogue = await StoryCatalogue.load(); });
  tearDownAll(() {
    final directory = Directory(_reportDirectory)..createSync(recursive: true);
    File('${directory.path}/matrix-results.json').writeAsStringSync(
      '${const JsonEncoder.withIndent('  ').convert({
        'schema_version': 1,
        'scope': 'Actual widget/card behavior across IDs and display conditions; not complete original asset acceptance',
        'expected_matrix_rows': 816,
        'observed_passing_matrix_rows': _rows.length,
        'complete_matrix_observed': _rows.length == 816,
        'conditions': _displays.map((d) => d.json).toList(),
        'rows': _rows,
        'supplemental_cases': _supplemental,
        'synthetic_paid_ownership': true,
        'external_store_or_rights_evidence': false,
        'canonical_verification_written': false,
      })}\n',
    );
  });

  test('catalogue identities and declared text palette contrast', () {
    expect(cosmeticCatalogue.length, 36);
    expect(cosmeticCatalogue.map((e) => e.id).toSet().length, 36);
    expect(producerScenes.length, 25);
    expect(producerScenes.map((e) => e['id']).toSet().length, 25);
    double contrast(Color foreground, Color background) {
      final a = foreground.computeLuminance(), b = background.computeLuminance();
      return ((a > b ? a : b) + .05) / ((a < b ? a : b) + .05);
    }
    final ratios = <String, double>{};
    for (final fg in {'text': TideColors.text, 'muted': TideColors.muted,
      'teal': TideColors.teal, 'amber': TideColors.amber, 'warning': TideColors.warning}.entries) {
      for (final bg in {'deep': TideColors.deep, 'panel': TideColors.panel, 'raised': TideColors.raised}.entries) {
        final ratio = contrast(fg.value, bg.value);
        ratios['${fg.key}_on_${bg.key}'] = ratio;
        expect(ratio, greaterThanOrEqualTo(4.5),
            reason: 'Declared opaque normal-text pair ${fg.key}/${bg.key}');
      }
    }
    final buyBackground = Color.alphaBlend(TideColors.teal.withValues(alpha: .14), TideColors.panel);
    ratios['teal_on_actual_build_button'] = contrast(TideColors.teal, buyBackground);
    expect(ratios['teal_on_actual_build_button'], greaterThanOrEqualTo(4.5));
    _supplemental.add({'case': 'declared_text_palette', 'ratios': ratios,
      'limit': 'Opaque palette and actual build-button composite only; not every pixel, icon, focus indicator, opacity, or human contrast/readability acceptance.'});
  });

  testWidgets('actual app animation responds to normal reduced motion and lifecycle disposal', (tester) async {
    const display = _Display('phone', Size(320, 720), 1, false);
    _configure(tester, display);
    final game = GameController(startTicker: false, clock: () => _clock);
    addTearDown(game.dispose);
    await _showApp(tester, game, display);
    final first = tester.widget<HarborArt>(find.byType(HarborArt)).phase;
    await tester.pump(const Duration(milliseconds: 400));
    final animated = tester.widget<HarborArt>(find.byType(HarborArt)).phase;
    expect(animated, isNot(first), reason: 'Default motion is actually animated.');
    final before = game.state.toJson();
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.hidden);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
    await tester.pump();
    final paused = tester.widget<HarborArt>(find.byType(HarborArt)).phase;
    await tester.pump(const Duration(milliseconds: 400));
    expect(tester.widget<HarborArt>(find.byType(HarborArt)).phase, paused,
        reason: 'Backgrounded host must not advance decorative animation.');
    expect(game.state.toJson(), before);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await _frames(tester);
    final resumed = tester.widget<HarborArt>(find.byType(HarborArt)).phase;
    await tester.pump(const Duration(milliseconds: 400));
    expect(tester.widget<HarborArt>(find.byType(HarborArt)).phase, isNot(resumed));
    tester.platformDispatcher.accessibilityFeaturesTestValue = const FakeAccessibilityFeatures(disableAnimations: true);
    await _frames(tester);
    final reduced = tester.widget<HarborArt>(find.byType(HarborArt)).phase;
    await tester.pump(const Duration(milliseconds: 400));
    expect(tester.widget<HarborArt>(find.byType(HarborArt)).phase, reduced);
    expect(game.state.toJson(), before);
    await _disposeView(tester);
    _supplemental.add({'case': 'actual_app_animation_lifecycle', 'normal_phase_changes': true,
      'background_phase_stops': true, 'resume_phase_restarts': true,
      'os_reduce_motion_stops': true, 'economic_state_unchanged_at_fixed_clock': true,
      'disposed_transient_callbacks': 0,
      'limit': 'Host lifecycle dispatch at a fixed synthetic clock, not physical background scheduling or power measurement.'});
  });

  for (final display in _displays) {
    testWidgets('harbor7 actual route ${display.id}', (tester) async {
      _configure(tester, display);
      final semantics = tester.ensureSemantics();
      addTearDown(semantics.dispose);
      for (var restoration = 0; restoration <= 6; restoration++) {
        final completed = {for (var i = 1; i <= restoration; i++) 'chapter.${i.toString().padLeft(2, '0')}'};
        final game = GameController(
          startTicker: false, clock: () => _clock,
          initialStory: StoryProgress(campaign: CampaignProgress(completed: completed)),
          initialState: GameState(counts: [10, 10, 10, 10, 10]),
        );
        final before = game.state.toJson();
        await _showApp(tester, game, display);
        final harbor = find.byType(HarborArt);
        await tester.ensureVisible(harbor);
        await _frames(tester);
        final widget = tester.widget<HarborArt>(harbor);
        expect(widget.restoration, restoration);
        expect(widget.counts, [10, 10, 10, 10, 10]);
        final label = tester.getSemantics(harbor).getSemanticsData().label;
        expect(label, contains('$restoration'));
        expect(label, contains('5'));
        expect(tester.getRect(harbor).width, greaterThan(100));
        final phase = widget.phase;
        await tester.pump(const Duration(milliseconds: 300));
        final later = tester.widget<HarborArt>(harbor).phase;
        expect(later == phase, display.reducedMotion);
        expect(game.state.toJson(), before);
        _row(restoration == 0 ? 'asset.harbor.unlit' : 'asset.harbor.restored.${restoration.toString().padLeft(2, '0')}',
          'harbor', display, {'actual_consumer': 'TideglassApp harbor', 'restoration': restoration,
          'image_semantics_label': label, 'motion_behavior_checked': true,
          'economic_state_unchanged': true, 'layout_exception': false});
        await _disposeView(tester);
        game.dispose();
      }
    });

    testWidgets('producer25 actual purchase cards ${display.id}', (tester) async {
      _configure(tester, display);
      final semantics = tester.ensureSemantics();
      addTearDown(semantics.dispose);
      for (var stage = 0; stage < 5; stage++) {
        final count = stage == 0 ? 10 : stage * 25;
        final game = GameController(startTicker: false, clock: () => _clock,
          initialState: GameState(counts: List.filled(5, count), walletMicros: BigInt.from(10).pow(35)));
        final before = game.state.toJson();
        await _showApp(tester, game, display);
        for (var tier = 0; tier < 5; tier++) {
          final card = find.byKey(ValueKey('producer-$tier'));
          final artFinder = find.descendant(of: card, matching: find.byType(StagedProducerArt));
          await tester.ensureVisible(artFinder);
          await _frames(tester);
          final art = tester.widget<StagedProducerArt>(artFinder);
          expect(art.tier, tier); expect(producerStageForCount(art.count), stage);
          expect(art.locked, isFalse);
          final painter = tester.widget<CustomPaint>(find.descendant(of: artFinder, matching: find.byType(CustomPaint))).painter! as ProducerStagePainter;
          expect(painter.tier, tier); expect(painter.stage, stage);
          expect(find.descendant(of: card, matching: find.text(UiEnglish.producerNames[tier])), findsOneWidget);
          final buy = find.byKey(ValueKey('buy-$tier'));
          await _reachable(tester, buy, display);
          expect(tester.widget<FilledButton>(buy).onPressed, isNotNull);
          expect(game.state.toJson(), before, reason: 'Showing art/scrolling did not buy anything.');
          _row('asset.producer.${(tier + 1).toString().padLeft(2, '0')}.stage.$stage', 'producer', display,
            {'actual_consumer': 'TideglassApp producer-$tier', 'count': count, 'painter_stage': stage,
            'adjacent_name': UiEnglish.producerNames[tier], 'purchase_button_reachable': true,
            'button_semantics_and_48px_hitbox': true, 'economic_state_unchanged': true,
            'layout_exception': false});
        }
        await _disposeView(tester); game.dispose();
      }
      // A valid initial fleet has only stage-zero locks. Past-stage lock and
      // selected rendering are separately labelled component stress variants.
      final lockedGame = GameController(startTicker: false, clock: () => _clock);
      await _showApp(tester, lockedGame, display);
      for (var tier = 1; tier < 5; tier++) {
        final card = find.byKey(ValueKey('producer-$tier'));
        await tester.ensureVisible(card); await _frames(tester);
        expect(find.descendant(of: card, matching: find.byIcon(Icons.lock_outline)), findsWidgets);
        expect(find.descendant(of: card, matching: find.textContaining('Needs 10')), findsOneWidget);
        expect(find.byKey(ValueKey('buy-$tier')), findsNothing);
      }
      await _disposeView(tester); lockedGame.dispose();
      _supplemental.add({'case': 'actual_initial_producer_locks', ...display.json,
        'tiers': [1, 2, 3, 4], 'non_color_icon_and_requirement_text': true, 'unavailable_purchase_absent': true});
    });

    testWidgets('producer25 selected locked component variants ${display.id}', (tester) async {
      _configure(tester, display);
      for (var tier = 0; tier < 5; tier++) {
        for (var stage = 0; stage < 5; stage++) {
          for (final locked in [false, true]) {
            final art = StagedProducerArt(tier: tier, count: stage * 25,
              size: 72, locked: locked, selected: true);
            await _showScreen(tester, Scaffold(body: SingleChildScrollView(child: Column(children: [
              art,
              Text('${UiEnglish.producerNames[tier]} · stage $stage'),
              Text(locked ? 'Locked · synthetic component state' : 'Selected · synthetic component state'),
            ]))), display);
            final stack = find.descendant(of: find.byType(StagedProducerArt), matching: find.byType(Stack));
            expect(stack, findsOneWidget);
            expect(find.descendant(of: stack, matching: find.byType(DecoratedBox)), findsOneWidget);
            expect(find.descendant(of: stack, matching: find.byIcon(Icons.lock_outline)), locked ? findsOneWidget : findsNothing);
            final painter = tester.widget<CustomPaint>(find.descendant(of: stack, matching: find.byType(CustomPaint))).painter! as ProducerStagePainter;
            expect(painter.tier, tier); expect(painter.stage, stage);
          }
        }
      }
      await _disposeView(tester);
      _supplemental.add({'case': 'selected_locked_component_matrix', ...display.json, 'producer_ids': 25,
        'selected': true, 'locked_states': [false, true],
        'limit': 'Selected state and high-stage locks are component fixtures; no claim of a reachable production selection route or valid high-stage locked save.'});
    });

    testWidgets('cosmetic36 locked owned equipped preview thumbnail ${display.id}', (tester) async {
      _configure(tester, display);
      final semantics = tester.ensureSemantics(); addTearDown(semantics.dispose);
      for (final item in cosmeticCatalogue) {
        final syntheticPaid = <String>{};
        final game = GameController(catalogue: catalogue, startTicker: false, clock: () => _clock,
          verifiedPaidCosmetics: () => syntheticPaid,
          initialState: GameState(walletMicros: BigInt.from(123000000),
            daily: DailyState(passXpById: {'pass.01': BigInt.from(15000)})));
        var purchases = 0;
        final offer = CosmeticStoreOffer(productId: 'fixture.${item.id}', productTitle: 'Synthetic provider offer', localizedPrice: 'TEST 4.99', cosmeticIds: {item.id});
        Widget screen() => ListenableBuilder(listenable: game, builder: (context, _) => CosmeticsScreen(
          ownedIds: game.ownedCosmetics, equippedId: game.visibleAppearance,
          equippedDecorationId: game.story.equippedDecoration,
          onEquip: (id) => game.equipCosmetic(id), onUnequipDecoration: game.unequipDecoration,
          offers: item.paid ? [offer] : [], onPurchase: item.paid ? (_) async { purchases++; } : null,
          previewCounts: const [25, 25, 10, 10, 1], restoration: 6,
        ));
        final economicLocked = game.state.toJson();
        await _showScreen(tester, screen(), display);
        final card = find.byKey(ValueKey('collection-${item.id}'));
        final preview = find.descendant(of: card, matching: find.byType(CosmeticPreview));
        await tester.ensureVisible(preview); await _frames(tester);
        expect(tester.widget<CosmeticPreview>(preview).id, item.id);
        expect(find.byKey(ValueKey('equip-${item.id}')), findsNothing);
        expect(find.descendant(of: card, matching: find.text(item.unlockLabel)), findsOneWidget);
        await tester.tap(preview); await tester.pump(const Duration(milliseconds: 400)); await _frames(tester);
        final dialog = find.byType(Dialog);
        expect(dialog, findsOneWidget);
        expect(tester.widget<CosmeticPreview>(find.descendant(of: dialog, matching: find.byType(CosmeticPreview))).id, item.id);
        final imageLabel = tester.getSemantics(find.descendant(of: dialog, matching: find.byType(CosmeticPreview))).getSemanticsData().label;
        expect(imageLabel, contains(item.title));
        final close = find.descendant(of: dialog, matching: find.byType(CloseButton));
        await _reachable(tester, close, display);
        await tester.tap(close); await tester.pump(const Duration(milliseconds: 400)); await _frames(tester);
        expect(game.ownedCosmetics.contains(item.id), isFalse);
        if (item.paid) {
          final buy = find.byKey(ValueKey('purchase-${item.id}-${offer.productId}'));
          await _reachable(tester, buy, display);
          await tester.tap(buy); await _frames(tester);
          expect(purchases, 1);
          expect(game.ownedCosmetics.contains(item.id), isFalse,
              reason: 'A synthetic purchase callback is not delivery.');
        }
        expect(game.state.toJson(), economicLocked);
        // Explicit ownership fixture or real free-pass claim, never a store grant.
        switch (item.source) {
          case CosmeticSource.chapter:
            game.story = game.story.copyWith(campaign: CampaignProgress(completed: {
              for (var i = 1; i <= item.ordinal; i++) 'chapter.${i.toString().padLeft(2, '0')}',
            }));
          case CosmeticSource.decoration:
            game.story = game.story.copyWith(decorations: {item.id});
          case CosmeticSource.freePass:
            final reward = catalogue.seasonDefinition.rewards.firstWhere((r) => r.contentId == item.id);
            expect(game.claimFreePassReward(reward.id), isTrue);
          case CosmeticSource.premiumPass:
          case CosmeticSource.shop:
            syntheticPaid.add(item.id);
        }
        expect(game.ownedCosmetics.contains(item.id), isTrue);
        final economicOwned = game.state.toJson();
        await _showScreen(tester, screen(), display);
        expect(find.descendant(of: card, matching: find.text('Kept in your collection')), findsOneWidget);
        final equip = find.byKey(ValueKey('equip-${item.id}'));
        await _reachable(tester, equip, display);
        await tester.tap(equip); await _frames(tester);
        expect(item.source == CosmeticSource.decoration ? game.story.equippedDecoration : game.visibleAppearance, item.id);
        expect(find.descendant(of: card, matching: find.text('Equipped')), findsOneWidget);
        expect(find.byKey(ValueKey('equip-${item.id}')), findsNothing);
        expect(game.state.toJson(), economicOwned);
        await _showApp(tester, game, display);
        if (item.source == CosmeticSource.decoration) {
          expect(tester.widget<HarborArt>(find.byType(HarborArt)).decoration, item.id);
        } else {
          final overlay = find.byType(CosmeticOverlay);
          expect(overlay, findsOneWidget);
          expect(tester.widget<CosmeticOverlay>(overlay).id, item.id);
          expect(tester.widget<IgnorePointer>(find.descendant(of: overlay, matching: find.byType(IgnorePointer))).ignoring, isTrue);
        }
        expect(game.state.toJson(), economicOwned);
        // Same actual preview component at thumbnail size; there is no claim
        // that the product currently has a separate 160px thumbnail route.
        await _showScreen(tester, Scaffold(body: SingleChildScrollView(child: Column(children: [
          SizedBox(width: 160, child: CosmeticPreview(id: item.id)),
          Text(item.title), const Text('Component thumbnail fixture'),
        ]))), display);
        final small = find.byType(CosmeticPreview);
        expect(tester.widget<CosmeticPreview>(small).id, item.id);
        expect(tester.getSize(small).width, 160);
        expect(tester.widget<CosmeticOverlay>(find.descendant(of: small, matching: find.byType(CosmeticOverlay))).id, item.id);
        expect(tester.getSemantics(small).getSemanticsData().label, contains(item.title));
        expect(game.state.toJson(), economicOwned);
        _row('asset.${item.id}', 'cosmetic', display, {
          'actual_consumers': ['CosmeticsScreen card', 'full preview dialog', 'TideglassApp equipped harbor'],
          'states': ['locked', 'owned', 'equipped'], 'same_id_across_consumers': true,
          'explicit_status_text': true, 'controls_reachable_with_48px_button_semantics': true,
          'preview_image_semantics': imageLabel, 'thumbnail_width': 160,
          'thumbnail_is_component_fixture': true, 'synthetic_paid_authority': item.paid,
          'purchase_callback_does_not_grant': item.paid ? true : null,
          'economic_state_unchanged_by_presentation_and_equip': true, 'layout_exception': false,
        });
        await _disposeView(tester); game.dispose();
      }
    }, timeout: const Timeout(Duration(minutes: 12)));
  }
}
