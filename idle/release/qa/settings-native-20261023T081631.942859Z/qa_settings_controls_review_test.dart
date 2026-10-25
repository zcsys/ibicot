import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/audio_bus.dart';
import 'package:tideglass/audio_settings.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/harbor_art.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass_core/tideglass_core.dart';

import '../../../game/mobile/test/audio_bus_test.dart'
    show FakeAudioDriver, MemoryAudioStore;

// Staged reviewer probe. No native adapter, external service or shared write.
void main() {
  for (final size in [const Size(390, 844), const Size(1024, 768)]) {
    testWidgets('actual settings controls and keyboard purchase at $size', (
      tester,
    ) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      tester.platformDispatcher.textScaleFactorTestValue = 1.5;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      final semantics = tester.ensureSemantics();
      final driver = FakeAudioDriver(), store = MemoryAudioStore();
      final audio = TideAudioBus(
        driver: driver,
        store: store,
        observeLifecycle: false,
      );
      await audio.initialize();
      await audio.startMusic(TideMusic.harbor);
      final game = GameController(
        initialState: GameState(
          walletMicros: BigInt.from(15000000000),
          lifetimeMicros: BigInt.from(15000000000),
        ),
        audio: audio,
        startTicker: false,
        clock: () => DateTime.utc(2026, 10, 23),
      );
      var saved = const ClientPreferences(onboardingDismissed: true);
      var writes = 0;
      Future<void> frame() async {
        // Initial normal-motion harbor loops deliberately; never pumpAndSettle
        // until the user has actually enabled reduced motion.
        await tester.pump(const Duration(milliseconds: 400));
        await tester.pump();
      }

      Finder text(String value) => find.text(Presentation.text(value));
      Finder tile(String label) =>
          find.ancestor(of: text(label), matching: find.byType(SwitchListTile));
      Future<void> tap(Finder target) async {
        expect(target, findsOneWidget);
        await tester.ensureVisible(target);
        await frame();
        final box = tester.getRect(target);
        expect(box.width, greaterThanOrEqualTo(48));
        expect(box.height, greaterThanOrEqualTo(48));
        await tester.tap(target);
        await frame();
      }

      Future<void> keyboardActivate(Finder target) async {
        final element = tester.element(target);
        bool containsPrimaryFocus() {
          var found = false;
          final context = FocusManager.instance.primaryFocus?.context;
          if (identical(context, element)) return true;
          context?.visitAncestorElements((ancestor) {
            if (identical(ancestor, element)) {
              found = true;
              return false;
            }
            return true;
          });
          return found;
        }

        for (var n = 0; n < 100 && !containsPrimaryFocus(); n++) {
          await tester.sendKeyEvent(LogicalKeyboardKey.tab);
          await frame();
        }
        expect(
          containsPrimaryFocus(),
          true,
          reason: 'actual sequential keyboard focus reaches target',
        );
        await tester.sendKeyEvent(LogicalKeyboardKey.space);
        await frame();
      }

      try {
        await tester.pumpWidget(
          TideglassApp(
            controller: game,
            initialPreferences: saved,
            onPreferencesChanged: (value) async {
              saved = ClientPreferences.fromJson(value.toJson());
              writes++;
            },
          ),
        );
        await frame();
        expect(text('15.0K'), findsOneWidget);
        final before = jsonEncode(game.state.toJson());
        expect(tester.binding.transientCallbackCount, greaterThan(0));
        await tap(find.byTooltip(Presentation.text(Copy.settings)));
        await tap(tile(Copy.reducedMotion));
        expect(saved.reduceMotion, true);
        expect(
          MediaQuery.disableAnimationsOf(
            tester.element(tile(Copy.reducedMotion)),
          ),
          true,
        );
        await frame();
        final phaseBefore = tester
            .widget<HarborArt>(find.byType(HarborArt))
            .phase;
        await tester.pump(const Duration(seconds: 1));
        final phaseAfter = tester
            .widget<HarborArt>(find.byType(HarborArt))
            .phase;
        expect(phaseAfter, phaseBefore);
        // Check the actual decorative phase; allow transient control/route
        // callbacks to settle before the separate no-continuing-ticker check.
        expect(tester.binding.transientCallbackCount, 0);
        await tap(tile(Copy.largerText));
        expect(saved.largeText, true);
        expect(
          MediaQuery.textScalerOf(tester.element(tile(Copy.largerText)))
              .scale(10),
          closeTo(18, 1e-9),
        );
        await keyboardActivate(tile(Copy.scientific));
        expect(saved.scientific, true);
        expect(writes, 3);

        await tap(tile(UiEnglish.audioMusic));
        expect(audio.preferences.musicMuted, true);
        expect(audio.preferences.effectiveMusic, 0);
        await tap(tile(UiEnglish.audioMusic));
        expect(audio.preferences.musicMuted, false);
        await tap(tile(UiEnglish.audioSoundEffects));
        expect(audio.preferences.sfxMuted, true);
        expect(await audio.playCue(TideCue.claim), false);
        await tap(tile(UiEnglish.audioSoundEffects));
        expect(audio.preferences.sfxMuted, false);

        final sliders = find.descendant(
          of: find.byType(AudioSettings),
          matching: find.byType(Slider),
        );
        expect(sliders, findsNWidgets(2));
        for (var i = 0; i < 2; i++) {
          final slider = sliders.at(i);
          await tester.ensureVisible(slider);
          await frame();
          final initial = tester.widget<Slider>(slider).value;
          final rect = tester.getRect(slider);
          await tester.tapAt(
            Offset(
              rect.left + rect.width * (i == 0 ? .75 : .25),
              rect.center.dy,
            ),
          );
          await frame();
          final changed = tester.widget<Slider>(slider).value;
          expect(changed, inInclusiveRange(0, 1));
          expect(changed, isNot(initial));
          expect(
            i == 0 ? store.value!.musicVolume : store.value!.sfxVolume,
            changed,
          );
          expect(i == 0 ? driver.musicVolume : driver.sfxVolume, changed);
        }
        await tap(tile(UiEnglish.audioMuteAllSound));
        expect(audio.preferences.muted, true);
        expect(store.value!.muted, true);
        expect(await audio.playCue(TideCue.claim), false);
        expect(driver.stopMusicCount, greaterThan(0));
        expect(driver.stopCueCount, greaterThan(0));
        expect(jsonEncode(game.state.toJson()), before);
        await tap(
          find.ancestor(
            of: text(UiCopy.returnToTheHarbor),
            matching: find.byType(FilledButton),
          ),
        );
        expect(text('1.50e4'), findsOneWidget);
        expect(
          MediaQuery.disableAnimationsOf(tester.element(text('1.50e4'))),
          true,
        );
        expect(
          MediaQuery.textScalerOf(tester.element(text('1.50e4'))).scale(10),
          closeTo(18, 1e-9),
        );
        final preBuy = game.state;
        await keyboardActivate(find.byKey(const ValueKey('buy-0')));
        expect(game.state.counts, [2, 0, 0, 0, 0]);
        expect(
          game.state.walletMicros,
          preBuy.walletMicros - BigInt.from(33600000),
        );
        expect(game.state.lifetimeMicros, preBuy.lifetimeMicros);
        expect(tester.takeException(), isNull);
      } finally {
        await tester.pumpWidget(const SizedBox.shrink());
        semantics.dispose();
        game.dispose();
        await audio.close();
        audio.dispose();
      }
    });
  }
}
