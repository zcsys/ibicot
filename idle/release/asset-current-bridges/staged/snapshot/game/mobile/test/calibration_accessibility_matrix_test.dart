import 'dart:convert';
import 'dart:io';
import 'dart:ui' show SemanticsAction;

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/calibration_pattern.dart';
import 'package:tideglass/calibration_screen.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';

import 'calibration_test.dart' show allPatterns, solve;

// Stage this file in game/mobile/test before running. Fixtures are produced by
// actual core transitions at a fixed synthetic clock, never participant data.
// The same suite must run in both compile-time presentation modes.
const _locale = Presentation.pseudoEnabled ? 'qps-ploc' : 'en-US';
const _reportDirectory = String.fromEnvironment(
  'TIDEGLASS_ACCESSIBILITY_REPORT_DIR',
  defaultValue: '../../release/accessibility-current/author-$_locale',
);
const _engine = TideglassEngine();
final _clock = DateTime.utc(2026, 10, 21, 12);
final _rows = <Map<String, Object?>>[];

class _Display {
  const _Display(this.name, this.size, this.scale, this.reduced);
  final String name;
  final Size size;
  final double scale;
  final bool reduced;
  String get id =>
      '$_locale-$name-${(scale * 100).round()}-${reduced ? 'reduced' : 'normal'}';
  Map<String, Object?> get json => {
    'condition_id': id,
    'locale': _locale,
    'viewport': [size.width, size.height],
    'text_scale': scale,
    'reduced_motion': reduced,
  };
}

final _displays = [
  for (final viewport in {
    'phone': const Size(320, 720),
    'tablet': const Size(1024, 768),
  }.entries)
    for (final scale in [1.0, 1.5, 2.0])
      for (final reduced in [false, true])
        _Display(viewport.key, viewport.value, scale, reduced),
];

String _digest(Object value) =>
    sha256.convert(utf8.encode(jsonEncode(value))).toString();

void _configure(WidgetTester tester, _Display display) {
  tester.view.physicalSize = display.size;
  tester.view.devicePixelRatio = 1;
  tester.platformDispatcher.textScaleFactorTestValue = display.scale;
  tester.platformDispatcher.accessibilityFeaturesTestValue =
      FakeAccessibilityFeatures(disableAnimations: display.reduced);
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  addTearDown(tester.platformDispatcher.clearAccessibilityFeaturesTestValue);
}

Finder _key(String key) => find.byKey(ValueKey(key));
Finder _textButton(String text) => find.ancestor(
  of: find.text(Presentation.text(text)),
  matching: find.byWidgetPredicate((widget) => widget is TextButton),
);

Future<void> _frames(WidgetTester tester) async {
  await tester.pumpAndSettle();
  expect(tester.takeException(), isNull);
}

Future<void> _reachable(
  WidgetTester tester,
  Finder finder,
  _Display display, {
  bool enabled = true,
  bool chip = false,
}) async {
  expect(finder, findsOneWidget);
  await Scrollable.ensureVisible(tester.element(finder), alignment: .5);
  await _frames(tester);
  final rect = tester.getRect(finder);
  expect(rect.width, greaterThanOrEqualTo(48), reason: '48px control width');
  expect(rect.height, greaterThanOrEqualTo(48), reason: '48px control height');
  expect(rect.left, greaterThanOrEqualTo(-.5));
  expect(rect.right, lessThanOrEqualTo(display.size.width + .5));
  expect(rect.top, greaterThanOrEqualTo(-.5));
  expect(rect.bottom, lessThanOrEqualTo(display.size.height + .5));
  expect(finder.hitTestable(), findsOneWidget);
  final semantics = tester.getSemantics(finder).getSemanticsData();
  expect(semantics.label.trim(), isNotEmpty);
  if (!chip) expect(semantics.flagsCollection.isButton, isTrue);
  expect(semantics.hasAction(SemanticsAction.tap), enabled);
}

Future<void> _tap(
  WidgetTester tester,
  Finder finder,
  _Display display, {
  bool enabled = true,
  bool chip = false,
}) async {
  await _reachable(tester, finder, display, enabled: enabled, chip: chip);
  await tester.tap(finder.hitTestable());
  await _frames(tester);
}

Future<void> _unmount(WidgetTester tester) async {
  await tester.pumpWidget(const SizedBox.shrink());
  await _frames(tester);
  expect(tester.binding.transientCallbackCount, 0);
}

GameState _freshState() {
  // Three Focus charges come from six actual hours of core advancement.
  final earned = _engine.advance(GameState.initial(), const Duration(hours: 6));
  expect(earned.accepted, isTrue);
  final initialized = _engine.refreshContracts(
    earned.state,
    _clock,
    accountSeed: 'calibration-accessibility-fixture',
    utcOffsetMinutes: 0,
    availableDiscoveryKinds: ['archive', 'calibration'],
  );
  expect(initialized.accepted, isTrue);
  expect(initialized.state.focusCharges, 3);
  expect(
    GameState.fromJson(initialized.state.toJson()).toJson(),
    initialized.state.toJson(),
  );
  return initialized.state;
}

Future<void> _show(
  WidgetTester tester,
  List<CalibrationPattern> patterns,
  int index,
  GameController game,
  _Display display,
  bool Function(String) complete,
) async {
  await tester.pumpWidget(
    MaterialApp(
      key: UniqueKey(),
      theme: tideglassTheme(),
      home: CalibrationScreen(
        patterns: patterns,
        focusCharges: () => game.state.focusCharges,
        collectedIds: () => game.state.completedCalibrationIds,
        onComplete: complete,
      ),
    ),
  );
  await _frames(tester);
  final context = tester.element(find.byType(CalibrationScreen));
  expect(MediaQuery.sizeOf(context), display.size);
  expect(MediaQuery.textScalerOf(context).scale(10), display.scale * 10);
  expect(MediaQuery.disableAnimationsOf(context), display.reduced);
  final chip = find.byType(ChoiceChip).at(index);
  await _tap(tester, chip, display, chip: true);
  expect(tester.widget<ChoiceChip>(chip).selected, isTrue);
  expect(
    tester.widget<ChoiceChip>(chip).avatar != null,
    game.state.completedCalibrationIds.contains(patterns[index].id),
    reason: 'Previously earned status must be visible independently of color.',
  );
  expect(find.text(Presentation.text(patterns[index].title)), findsOneWidget);
  final sky = find.byWidgetPredicate(
    (widget) => widget is Semantics && widget.properties.image == true,
  );
  await Scrollable.ensureVisible(tester.element(sky), alignment: .5);
  await _frames(tester);
  final skyData = tester.getSemantics(sky).getSemanticsData();
  expect(skyData.flagsCollection.isImage, isTrue);
  expect(skyData.label, contains(Presentation.authored(patterns[index].title)));
}

Future<void> _solveWithRecovery(
  WidgetTester tester,
  CalibrationPattern pattern,
  _Display display,
) async {
  final route = solve(pattern, [pattern.start])!;
  final first = _key('star-${route[1]}');
  final undo = _textButton(UiEnglish.calibrationUndo);
  final restart = _textButton(UiEnglish.calibrationRestart);
  await _reachable(tester, undo, display, enabled: false);
  await _tap(tester, first, display);
  await _tap(tester, undo, display);
  expect(first, findsOneWidget, reason: 'Undo returns the same legal choice.');
  await _tap(tester, first, display);
  await _tap(tester, restart, display);
  expect(first, findsOneWidget, reason: 'Restart returns to the first star.');
  for (final key in route.skip(1)) {
    await _tap(tester, _key('star-$key'), display);
  }
  expect(
    find.text(
      Presentation.text(UiEnglish.calibrationTheConstellationIsAligned),
    ),
    findsOneWidget,
  );
}

Future<void> _equalCompletionRoutes(
  WidgetTester tester,
  List<CalibrationPattern> patterns,
  int index,
  StoryCatalogue catalogue,
  GameState initial,
  _Display display, {
  required bool alreadyEarned,
}) async {
  final pattern = patterns[index];
  final after = <Map<String, dynamic>>[];
  final stories = <Map<String, dynamic>>[];
  final durable = <Map<String, dynamic>>[];
  Map<String, dynamic>? baseline;
  for (final crew in [false, true]) {
    var commands = 0;
    final saves = <Map<String, dynamic>>[];
    final game = GameController(
      catalogue: catalogue,
      initialState: initial,
      startTicker: false,
      clock: () => _clock,
      onSessionPersist: (state, story, through) async {
        saves.add({
          'core': state.toJson(),
          'story': story.toJson(),
          'settled_through': through.toUtc().toIso8601String(),
        });
      },
    );
    try {
      final before = game.state;
      baseline ??= before.toJson();
      expect(
        before.toJson(),
        baseline,
        reason: 'Identical valid starting state.',
      );
      expect(
        before.completedCalibrationIds.contains(pattern.id),
        alreadyEarned,
      );
      await _show(tester, patterns, index, game, display, (id) {
        commands++;
        expect(id, pattern.id);
        return game.completeCalibration(id);
      });
      expect(game.state.toJson(), before.toJson());
      if (!crew) await _solveWithRecovery(tester, pattern, display);
      expect(
        game.state.toJson(),
        before.toJson(),
        reason: 'Practice is not a claim.',
      );
      expect(saves, isEmpty);
      await _tap(
        tester,
        _key(
          crew ? 'claim-accessible-calibration' : 'claim-routed-calibration',
        ),
        display,
      );
      expect(commands, 1);
      expect(game.state.focusCharges, before.focusCharges - 1);
      expect(
        game.state.focusRemainingMicros,
        before.focusRemainingMicros + BigInt.from(600000000),
      );
      expect(game.state.walletMicros, before.walletMicros);
      expect(game.state.lifetimeMicros, before.lifetimeMicros);
      expect(game.state.surveyNotes, before.surveyNotes);
      expect(game.state.passXp, before.passXp);
      expect(game.state.charts, before.charts);
      expect(game.state.counts, before.counts);
      expect(game.state.completedCalibrationIds, {
        ...before.completedCalibrationIds,
        pattern.id,
      });
      expect(
        game.state.daily.discoveryTotals['calibration'],
        (before.daily.discoveryTotals['calibration'] ?? BigInt.zero) +
            BigInt.one,
      );
      expect(
        game.state.nextDiscoverySequence,
        before.nextDiscoverySequence + BigInt.one,
      );
      expect(
        _engine.activeOutputPerSecond(game.state).raw,
        _engine.outputPerSecond(game.state).raw *
            BigInt.from(120) ~/
            BigInt.from(100),
      );
      expect(saves, hasLength(1));
      expect(saves.single['core'], game.state.toJson());
      expect(saves.single['story'], game.story.toJson());
      expect(
        tester.widget<ChoiceChip>(find.byType(ChoiceChip).at(index)).avatar,
        isNotNull,
        reason: 'The successful claim visibly marks this pattern as earned.',
      );
      final acceptedState = game.state.toJson();
      for (final claim in [
        'claim-routed-calibration',
        'claim-accessible-calibration',
      ]) {
        await _tap(tester, _key(claim), display, enabled: false);
      }
      expect(
        commands,
        1,
        reason: 'Neither completion control repeats this claim.',
      );
      expect(game.state.toJson(), acceptedState);
      expect(saves, hasLength(1));
      after.add(acceptedState);
      stories.add(game.story.toJson());
      durable.add(saves.single);
    } finally {
      try {
        await _unmount(tester);
      } finally {
        game.dispose();
      }
    }
  }
  expect(
    after[0],
    after[1],
    reason: 'Every exact core field is route-independent.',
  );
  expect(
    stories[0],
    stories[1],
    reason: 'Campaign/pass content is route-independent.',
  );
  expect(
    durable[0],
    durable[1],
    reason: 'The persisted session is route-independent.',
  );
  _rows.add({
    'pattern_id': pattern.id,
    ...display.json,
    'state': alreadyEarned ? 'previously_earned' : 'unearned',
    'normal_and_crew_core_story_persistence_equal': true,
    'single_charge_600_seconds_20_percent': true,
    'collectible_set_does_not_duplicate': true,
    'undo_restart_and_route_traversed': true,
    'duplicate_controls_disabled': true,
    'reachable_48px_controls_and_named_semantics': true,
    'layout_exception': false,
    'before_core_sha256': _digest(baseline!),
    'after_core_sha256': _digest(after[0]),
    'after_session_sha256': _digest(durable[0]),
    'result': 'passed_bounded_host_case',
  });
}

Future<void> _noFocusPractice(
  WidgetTester tester,
  List<CalibrationPattern> patterns,
  int index,
  StoryCatalogue catalogue,
  GameState initial,
  _Display display,
) async {
  final pattern = patterns[index];
  var commands = 0, saves = 0;
  late Map<String, Object?> row;
  final game = GameController(
    catalogue: catalogue,
    initialState: initial,
    startTicker: false,
    clock: () => _clock,
    onSessionPersist: (_, _, _) async {
      saves++;
    },
  );
  try {
    expect(game.state.focusCharges, 0);
    final before = game.state.toJson(), story = game.story.toJson();
    await _show(tester, patterns, index, game, display, (id) {
      commands++;
      return game.completeCalibration(id);
    });
    for (final claim in [
      'claim-routed-calibration',
      'claim-accessible-calibration',
    ]) {
      await _tap(tester, _key(claim), display, enabled: false);
    }
    await _solveWithRecovery(tester, pattern, display);
    for (final claim in [
      'claim-routed-calibration',
      'claim-accessible-calibration',
    ]) {
      await _tap(tester, _key(claim), display, enabled: false);
    }
    expect(commands, 0);
    expect(saves, 0);
    expect(game.state.toJson(), before);
    expect(game.story.toJson(), story);
    row = {
      'pattern_id': pattern.id,
      ...display.json,
      'state': 'no_stored_focus_practice',
      'full_route_undo_restart_work': true,
      'both_claims_disabled_before_and_after_solving': true,
      'commands': 0,
      'save_writes': 0,
      'complete_core_and_story_unchanged': true,
      'reachable_48px_controls_and_named_semantics': true,
      'layout_exception': false,
      'unchanged_core_sha256': _digest(before),
      'result': 'passed_bounded_host_case',
    };
  } finally {
    try {
      await _unmount(tester);
    } finally {
      game.dispose();
    }
  }
  _rows.add(row);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final patterns = allPatterns();
  late StoryCatalogue catalogue;
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  tearDownAll(() {
    final directory = Directory(_reportDirectory)..createSync(recursive: true);
    final sources = [
      'test/calibration_accessibility_matrix_test.dart',
      'test/calibration_test.dart',
      'lib/calibration_screen.dart',
      'lib/calibration_pattern.dart',
      'lib/game_controller.dart',
      'lib/story_state.dart',
      'lib/presentation.dart',
      'lib/strings.dart',
      'lib/palette.dart',
      '../core/lib/src/daily_engine.dart',
      '../core/lib/src/engine.dart',
      for (final pattern in patterns)
        'assets/calibrations/${pattern.id}.pattern.json',
    ];
    File('${directory.path}/calibration-matrix.json').writeAsStringSync(
      '${const JsonEncoder.withIndent('  ').convert({
        'schema_version': 1,
        'scope': 'M5-02/M3-04 S02/S09/S17/S26 bounded host interaction qualification',
        'locale': _locale,
        'pseudo_enabled': Presentation.pseudoEnabled,
        'expected_pattern_display_cases': 144,
        'expected_state_rows': 432,
        'observed_passing_state_rows': _rows.length,
        'complete_matrix_observed': _rows.length == 432,
        'runner_exit_status_is_also_required': true,
        'source_sha256': {for (final path in sources) path: sha256.convert(File(path).readAsBytesSync()).toString()},
        'conditions': _displays.map((d) => d.json).toList(),
        'rows': _rows,
        'limits': ['Synthetic fixed-clock controller fixtures, not human pacing or natural unlock proof.', 'Host semantics, hit-testing and layout only; not physical screen-reader or touch qualification.', 'Calibration artwork is static in both motion conditions; no animation claim.', 'Persistence callback equality, not a filesystem, cloud or provider durability test.', 'Compile-time English and pseudo require separate runs; passing rows are not scope acceptance.'],
      })}\n',
    );
  });
  for (final display in _displays) {
    for (var index = 0; index < patterns.length; index++) {
      final pattern = patterns[index];
      testWidgets('${pattern.id} exact routes earned practice ${display.id}', (
        tester,
      ) async {
        _configure(tester, display);
        final semantics = tester.ensureSemantics();
        try {
          final fresh = _freshState();
          await _equalCompletionRoutes(
            tester,
            patterns,
            index,
            catalogue,
            fresh,
            display,
            alreadyEarned: false,
          );
          final earned = _engine.completeCalibration(fresh, pattern.id);
          expect(earned.accepted, isTrue);
          expect(
            GameState.fromJson(earned.state.toJson()).toJson(),
            earned.state.toJson(),
          );
          await _equalCompletionRoutes(
            tester,
            patterns,
            index,
            catalogue,
            earned.state,
            display,
            alreadyEarned: true,
          );
          final noFocus = _engine.activateFocus(
            fresh,
            charges: fresh.focusCharges,
          );
          expect(noFocus.accepted, isTrue);
          await _noFocusPractice(
            tester,
            patterns,
            index,
            catalogue,
            noFocus.state,
            display,
          );
        } finally {
          semantics.dispose();
        }
      });
    }
  }
}
