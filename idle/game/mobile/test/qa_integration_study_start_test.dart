import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/study_gate.dart';
import 'package:tideglass_platform/study_recorder.dart';

class DelayedStartStore implements StudyStore {
  String? raw;
  bool hold = false;
  final entered = Completer<void>();
  final release = Completer<void>();
  @override
  Future<String?> read() async => raw;
  @override
  Future<bool> compareAndSwap(String? old, String next) async {
    if (hold) {
      if (!entered.isCompleted) entered.complete();
      await release.future;
    }
    if ((raw == null ? null : studyDigest(raw!)) != old) return false;
    raw = next;
    return true;
  }
}

class CountBootstrap extends StatelessWidget {
  const CountBootstrap(this.onBuild, {super.key});
  final VoidCallback onBuild;
  @override
  Widget build(BuildContext context) {
    onBuild();
    return const SizedBox();
  }
}

void main() {
  testWidgets('restored study start settles before ordinary bootstrap can build', (tester) async {
    final provisionText = jsonEncode({
      'study_id': 'qa-start', 'protocol_sha256': 'b' * 64,
      'candidate_sha256': 'a' * 64, 'config': 'qa-start',
      'consent_version': 'qa', 'information': 'Synthetic QA only.',
      'contact': 'https://example.invalid/study', 'retention': 'Temporary fixture.',
      'synthetic': true, 'device_group': 'unclassified', 'acquisition': 'internal_test',
    });
    final provision = StudyProvision.fromJson(jsonDecode(provisionText));
    final store = DelayedStartStore();
    var id = 0;
    final original = await StudyRecorder.open(store, idGenerator: () => (++id).toRadixString(16).padLeft(32, '0'));
    await original.enroll(provision.enrollment('e' * 64), provision.currentConfig, eligibleFreshInstall: true);
    final restored = await StudyRecorder.open(store, idGenerator: () => (++id).toRadixString(16).padLeft(32, '0'));
    store.hold = true;
    var boots = 0;
    await tester.pumpWidget(StudyGate(
      provision: provisionText,
      supportDirectory: Directory.systemTemp,
      openRecorder: (_) async => restored,
      child: CountBootstrap(() => boots++),
    ));
    await tester.pump();
    expect(store.entered.isCompleted, true);
    final duringPendingStart = boots;
    store.release.complete();
    await tester.pumpAndSettle();
    expect(duringPendingStart, 0, reason: 'An enrolled restart must record its start before the ordinary game bootstrap runs.');
    expect(boots, greaterThan(0));
    final rows = (jsonDecode(store.raw!) as Map)['records'] as List;
    expect(rows.where((r) => r['kind'] == 'app_start').length, 2);
  });
}
