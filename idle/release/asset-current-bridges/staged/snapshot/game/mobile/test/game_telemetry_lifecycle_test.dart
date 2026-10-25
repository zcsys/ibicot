import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'bootstrap_test.dart' show settleIo;
import 'game_telemetry_test.dart' show TelemetryClient;
import 'native_services_test.dart' show MemoryCredentials;

void main() {
  testWidgets('actual app lifecycle reports only the consented foreground', (
    tester,
  ) async {
    final client = TelemetryClient();
    final manager = NativeServicesManager(
      client: client,
      credentials: MemoryCredentials(),
    );
    var now = DateTime.utc(2026, 10, 19);
    final game = GameController(
      startTicker: false,
      clock: () => now,
      initialState: GameState.initial().copyWith(
        lifetimeMicros: TideglassEngine.firstPrestigeMicros,
        walletMicros: TideglassEngine.firstPrestigeMicros,
      ),
      onPersist: (_, _) async {},
    );
    await manager.createAccount(cloudConsent: true);
    await tester.pumpWidget(
      TideglassApp(
        controller: game,
        services: manager,
        initialPreferences: const ClientPreferences(reduceMotion: true),
      ),
    );
    await tester.pump();
    expect(client.events, isEmpty);
    await manager.setTelemetryConsent(true);
    int count(String name) =>
        client.events.where((e) => e['name'] == name).length;
    await settleIo(tester, until: () => count('session_start') == 1);
    expect(count('session_start'), 1);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
    await tester.pump();
    expect(count('session_end'), 0);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
    await settleIo(tester, until: () => count('session_end') == 1);
    expect(count('session_end'), 1);
    now = now.add(const Duration(hours: 4));
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await settleIo(tester, until: () => count('resume_result') == 1);
    expect(count('session_start'), 2);
    expect(count('resume_result'), 1);
    expect(
      client.consentWrites,
      1,
      reason: 'Returning reads consent; it never opts in again.',
    );
    expect(game.state.elapsedMicros, BigInt.from(14400000000));
    expect(game.rechart(), isTrue);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
    await settleIo(tester, until: () => count('session_end') == 2);
    expect(count('rechart'), 1);
    await tester.pumpWidget(const SizedBox());
    await tester.pump();
    expect(
      count('session_end'),
      2,
      reason: 'Widget disposal is not a clean process-exit observation.',
    );
    game.dispose();
    manager.dispose();
    client.close();
    expect(tester.takeException(), isNull);
  });
}
