from pathlib import Path
base=Path(__file__).resolve().parent
p=base/'staged/game/mobile/integration_test/native_reminders_test.dart'
s=p.read_text()
s=s.replace("const scenarios = {'default', 'denied', 'quiet-cancel', 'delivery', 'revoked'};", "const scenarios = {'default', 'denied', 'quiet-cancel', 'delivery', 'revoked',\n  'revoked-prepare', 'revoked-recover'};")
s=s.replace("    expect(scenarios, contains(scenario));", "    expect(scenarios, contains(scenario));\n    if (scenario.startsWith('revoked-')) expect(Platform.isAndroid, isTrue);")
s=s.replace("    final dir = Directory(\n      '${support.path}/native-reminders/$label-$runId-$scenario',\n    );", "    if (scenario == 'revoked-recover') {\n      await recoverRevoked(tester, support);\n      return;\n    }\n    final dir = Directory(\n      '${support.path}/native-reminders/$label-$runId-$scenario',\n    );")
s=s.replace("        } else if (scenario == 'revoked') {", """        } else if (scenario == 'revoked-prepare') {
          report['background_call_utc_ms'] = utcMs();
          await lifecycle.backgrounded();
          await recordPlan(service, gateway, repository, game);
          report['preferences_sha256'] = await fileDigest(preferenceFile);
          final checkpoint = <String, dynamic>{
            'version': 1,
            'preparation': report,
            'files_sha256': await restartFiles(dir),
            'written_utc_ms': utcMs(),
          };
          final file = File('${dir.path}/revoke-checkpoint.json');
          expect(await file.exists(), isFalse);
          await file.writeAsString(jsonEncode(checkpoint), flush: true);
          action('revoke_in_os_settings_expect_process_death', {
            'checkpoint': file.path,
            'checkpoint_sha256': await fileDigest(file),
          });
          await service.openDeviceSettings();
          // Android may terminate this process for PERMISSION CHANGE. This
          // preparation never reports a passed/completed integration test.
          await until(() => false,
              reason: 'Actual Android permission-change termination required.',
              seconds: 180);
        } else if (scenario == 'revoked') {""")
s += r'''

Future<String> fileDigest(File file) async =>
    sha256.convert(await file.readAsBytes()).toString();

Future<Map<String, String>> restartFiles(Directory dir,
    {bool includePreferences = true}) async {
  final files = <String, String>{};
  for (final relative in [
    if (includePreferences) 'notification_preferences.json',
    'save/progress.0.json', 'save/progress.1.json',
  ]) {
    final file = File('${dir.path}/$relative');
    if (await file.exists()) files[relative] = await fileDigest(file);
  }
  expect(files.keys.where((key) => key.startsWith('save/')), isNotEmpty);
  if (includePreferences) expect(files, contains('notification_preferences.json'));
  return files;
}

Future<List<int>> activeReminderIds(NativeNotificationGateway gateway) async =>
    (await gateway.plugin.getActiveNotifications())
        .where((item) => ReminderPlanner.ids.contains(item.id))
        .map((item) => item.id).toList()..sort();

Future<void> recoverRevoked(WidgetTester tester, Directory support) async {
  const priorId = String.fromEnvironment('TIDEGLASS_PREDECESSOR_ID');
  const checkpointDigest = String.fromEnvironment('TIDEGLASS_PREDECESSOR_CHECKPOINT');
  expect(RegExp(r'^[A-Za-z0-9_-]{1,160}$').hasMatch(priorId), isTrue);
  expect(RegExp(r'^[a-f0-9]{64}$').hasMatch(checkpointDigest), isTrue);
  final dir = Directory('${support.path}/native-reminders/$label-$runId-revoked-prepare');
  final checkpointFile = File('${dir.path}/revoke-checkpoint.json');
  expect(await dir.exists(), isTrue);
  expect(await fileDigest(checkpointFile), checkpointDigest);
  final checkpoint = (jsonDecode(await checkpointFile.readAsString()) as Map)
      .cast<String, dynamic>();
  expect(checkpoint['version'], 1);
  final prior = (checkpoint['preparation'] as Map).cast<String, dynamic>();
  for (final entry in {
    'verification_id': priorId, 'candidate_fingerprint': candidate,
    'harness_sha256': harness, 'scenario': 'revoked-prepare', 'run_id': runId,
    'device_label': label, 'platform': 'android',
  }.entries) { expect(prior[entry.key], entry.value); }
  expect(prior['completed'], isFalse);
  expect(prior['process_id'], isA<int>());
  expect(prior['process_id'], greaterThan(1));
  expect(pid, isNot(prior['process_id']));
  final hashes = (checkpoint['files_sha256'] as Map).cast<String, String>();
  expect(await restartFiles(dir), hashes);
  report.addAll({
    'fixture_directory': dir.path,
    'predecessor_verification_id': priorId,
    'predecessor_checkpoint_sha256': checkpointDigest,
    'previous_process_id': prior['process_id'],
    'recovery_files_before': await restartFiles(dir),
    'predecessor_default_opted_out': prior['default_opted_out'],
  });
  final store = FileNotificationPreferences(File('${dir.path}/notification_preferences.json'));
  expect((await store.load()).enabled, isTrue);
  final gateway = NativeNotificationGateway();
  final service = NotificationService(gateway: gateway, store: store);
  final observation = NativeLifecycleObservation();
  WidgetsBinding.instance.addObserver(observation);
  addTearDown(() async {
    WidgetsBinding.instance.removeObserver(observation);
    await gateway.cancelReminders();
    service.dispose();
    await tester.pumpWidget(const SizedBox.shrink());
  });
  await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Text(
      'Tideglass reminder restart qualification. Real permission denial; retained synthetic save.'))));
  report['permission_before_initialize'] = (await gateway.permission()).name;
  // Android may already have removed an alarm/notification on revocation.
  // Record that separately from what production initialization cancels.
  report['pending_before_initialize'] = await pending(gateway);
  report['active_before_initialize'] = await activeReminderIds(gateway);
  expect(report['permission_before_initialize'], 'denied');
  final initBaseline = observation.events.length;
  await service.initialize();
  await tester.pump();
  report['initialization_lifecycle_events'] = observation.events.skip(initBaseline).toList();
  expect(observation.events.skip(initBaseline).where((row) => row['state'] != 'resumed'), isEmpty);
  expect(service.warningKey, isNull);
  expect(service.permission, ReminderPermission.denied);
  expect(service.preferences.enabled, isTrue,
      reason: 'Remembered opt-in is distinct from denied effective permission.');
  report['permission_after_initialize'] = service.permission.name;
  report['remembered_opt_in_after_initialize'] = service.preferences.enabled;
  report['pending_after_initialize'] = await pending(gateway);
  report['active_after_initialize'] = await activeReminderIds(gateway);
  expect(report['pending_after_initialize'], isEmpty);
  expect(report['active_after_initialize'], isEmpty);
  final repository = SaveRepository(Directory('${dir.path}/save'),
      economicVersion: economyVersion, economicDigest: bundledEconomicDigest,
      validatePayload: (payload) { GameState.fromJson(payload); });
  final saved = (await repository.load()).snapshot;
  expect(saved, isNotNull);
  final observed = (prior['plan_observation'] as Map).cast<String, dynamic>();
  expect(saved!.payload, observed['saved_payload']);
  expect(saved.saveId, observed['saved_snapshot_id']);
  expect(saved.settledThrough.toUtc().microsecondsSinceEpoch,
      observed['saved_settled_through_utc_micros']);
  report['restored_snapshot_id'] = saved.saveId;
  report['restored_payload_sha256'] = sha256.convert(utf8.encode(jsonEncode(saved.payload))).toString();
  report['restored_settled_through_utc_micros'] = saved.settledThrough.toUtc().microsecondsSinceEpoch;
  // Use the real scheduling path with the preserved saved state. Do not save
  // or settle it again merely to test the OS permission gate.
  await service.scheduleForAbsence(state: GameState.fromJson(saved.payload),
      settledThrough: saved.settledThrough);
  expect(service.permission, ReminderPermission.denied);
  expect(service.planned, isEmpty);
  report['denied_schedule_pending_ids'] = await pending(gateway);
  report['denied_schedule_active_ids'] = await activeReminderIds(gateway);
  expect(report['denied_schedule_pending_ids'], isEmpty);
  expect(report['denied_schedule_active_ids'], isEmpty);
  await service.onReturn();
  report['recovery_files_before_reoptin'] = await restartFiles(dir);
  expect(report['recovery_files_before_reoptin'], hashes);
  action('deny_permission_again_if_prompted');
  await service.enableByPlayer().timeout(const Duration(seconds: 150));
  expect(service.permission, ReminderPermission.denied);
  expect((await store.load()).enabled, isFalse);
  report['permission_after_reoptin'] = service.permission.name;
  report['preferences_after_reoptin'] = (await store.load()).toJson();
  report['preferences_sha256'] = await fileDigest(File('${dir.path}/notification_preferences.json'));
  report['recovery_save_files_after'] = await restartFiles(dir, includePreferences: false);
  expect(report['recovery_save_files_after'], Map<String, String>.from(hashes)
      ..remove('notification_preferences.json'));
  expect(await fileDigest(checkpointFile), checkpointDigest);
  report['return_pending_ids'] = await pending(gateway);
  report['return_active_ids'] = await activeReminderIds(gateway);
  expect(report['return_pending_ids'], isEmpty);
  expect(report['return_active_ids'], isEmpty);
  report['lifecycle_events'] = observation.events;
  report['completed'] = true;
}
'''
p.write_text(s)
