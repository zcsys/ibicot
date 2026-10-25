import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/service_settings.dart';
import 'package:tideglass_platform/tideglass_platform.dart';

const accountId = '10000000-0000-4000-8000-000000000001';
const firstSave = '20000000-0000-4000-8000-000000000001';
const secondSave = '20000000-0000-4000-8000-000000000002';
const firstBranch = '30000000-0000-4000-8000-000000000001';
const secondBranch = '30000000-0000-4000-8000-000000000002';

class LoopbackHttpOverrides extends HttpOverrides {}

class MemoryCredentials implements CredentialStore {
  final values = <String, String>{};
  @override
  Future<String?> read(String key) async => values[key];
  @override
  Future<void> write(String key, String value) async => values[key] = value;
  @override
  Future<void> delete(String key) async => values.remove(key);
}

Map<String, dynamic> cloudJson({int generation = 7, String? selected}) => {
  'generation': generation,
  'selected_save_id': selected,
  'selection_required': selected == null,
  'snapshots': [
    for (final row in [
      (firstSave, firstBranch, 12),
      (secondSave, secondBranch, 19),
    ])
      {
        'save_id': row.$1,
        'branch_id': row.$2,
        'revision': row.$3,
        'parent_id': null,
        'settled': '2026-10-16T10:30:00.123456Z',
        'digest': 'fixture-digest',
        'is_tip': true,
      },
  ],
};

/// Named fixture exercises the real native manager and UI. Never connects to its
/// reserved origin, and never manufactures store ownership.
class FixtureClient extends TideglassServiceClient {
  FixtureClient()
    : super(endpoint: Uri.parse('https://service.example.invalid'));
  final calls = <String>[];
  bool conflict = false, offline = false, loseRotationReply = false;
  String? rotatedCode, selected, uploaded;
  int generation = 7;
  bool remoteTelemetry = false;
  String currentCode = 'fixture-recovery-code';
  ServiceSession connect() => session = ServiceSession(
    accountId: accountId,
    token: 'secret-session-token-not-for-ui',
    expiresAt: DateTime.utc(2035),
  );
  @override
  Future<AccountCreated> createAccount({required bool cloudConsent}) async {
    calls.add('create:$cloudConsent');
    return AccountCreated(connect(), currentCode);
  }

  @override
  Future<ServiceSession> recoverAccount({
    required String accountId,
    required String recoveryCode,
  }) async {
    calls.add('recover');
    if (accountId != '10000000-0000-4000-8000-000000000001' ||
        recoveryCode != currentCode) {
      throw const ServiceException('invalid_recovery', status: 403);
    }
    return connect();
  }

  @override
  Future<CloudIndex> cloudIndex() async {
    calls.add('index');
    return CloudIndex.fromJson(
      cloudJson(generation: generation, selected: selected),
    );
  }

  @override
  Future<CloudIndex> uploadSnapshot(
    String exportedSave, {
    required int expectedGeneration,
  }) async {
    calls.add('upload:$expectedGeneration');
    if (conflict || expectedGeneration != generation) {
      throw const ServiceException('generation_changed', status: 409);
    }
    uploaded = exportedSave;
    generation++;
    return cloudIndex();
  }

  @override
  Future<String> downloadSnapshot(String saveId) async {
    calls.add('download:$saveId');
    return 'cloud-export-$saveId';
  }

  @override
  Future<CloudIndex> selectSnapshot(
    String saveId, {
    required int expectedGeneration,
    required bool confirmSelection,
  }) async {
    calls.add('select:$saveId:$expectedGeneration:$confirmSelection');
    if (conflict || expectedGeneration != generation) {
      throw const ServiceException('generation_changed', status: 409);
    }
    selected = saveId;
    generation++;
    return cloudIndex();
  }

  @override
  Future<AccountCreated> rotateRecoveryCode(
    String currentCode, {
    required String newRecoveryCode,
  }) async {
    calls.add('rotate');
    expect(currentCode, this.currentCode);
    rotatedCode = newRecoveryCode;
    this.currentCode = newRecoveryCode;
    if (loseRotationReply) throw const ServiceException('service_timeout');
    return AccountCreated(connect(), newRecoveryCode);
  }

  @override
  Future<void> signOut({bool allDevices = false}) async {
    calls.add('revoke');
    if (offline) throw const ServiceException('service_unavailable');
    session = null;
  }

  @override
  Future<void> deleteAccount({
    required String recoveryCode,
    required bool confirmDelete,
  }) async {
    calls.add('delete:$confirmDelete');
    if (!confirmDelete || recoveryCode != currentCode) {
      throw const ServiceException('invalid_recovery', status: 403);
    }
    session = null;
  }

  @override
  Future<Map<String, dynamic>> exportAccount() async {
    calls.add('export-account');
    return {
      'account_id': accountId,
      'cloud_saves': ['fixture-save-data'],
    };
  }

  @override
  Future<int> setTelemetryConsent(bool enabled) async {
    calls.add('telemetry:$enabled');
    if (offline) throw const ServiceException('service_unavailable');
    remoteTelemetry = enabled;
    return calls.length;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  Future<NativeServicesManager> managerFor(
    FixtureClient client, {
    bool signedIn = true,
    MemoryCredentials? storage,
  }) async {
    final manager = NativeServicesManager(
      client: client,
      credentials: storage ?? MemoryCredentials(),
    );
    await manager.initialize();
    if (signedIn) {
      await manager.createAccount(cloudConsent: true);
      await manager.acknowledgeRecoveryCode();
      client.calls.clear();
    }
    addTearDown(manager.dispose);
    return manager;
  }

  Future<void> show(
    WidgetTester tester,
    NativeServicesManager manager, {
    bool large = false,
    Future<String> Function()? export,
    Future<void> Function(String)? import,
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
            textScaler: TextScaler.linear(large ? 2 : 1),
            disableAnimations: true,
          ),
          child: child!,
        ),
        home: ServiceSettings(
          manager: manager,
          onExportHarbor: export ?? () async => 'local-fixture-harbor',
          onImportHarbor: import ?? (_) async {},
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> reveal(WidgetTester tester, Finder finder) async {
    final dialog = find.byKey(const ValueKey('service-dialog-scroll'));
    final list = dialog.evaluate().isNotEmpty
        ? dialog
        : find.byKey(const ValueKey('services-scroll'));
    final scrollable = find
        .descendant(of: list, matching: find.byType(Scrollable))
        .first;
    tester.state<ScrollableState>(scrollable).position.jumpTo(0);
    await tester.pump();
    await tester.scrollUntilVisible(
      finder,
      250,
      scrollable: scrollable,
      maxScrolls: 100,
    );
    await tester.pumpAndSettle();
  }

  Future<void> tap(WidgetTester tester, String key) async {
    final finder = find.byKey(ValueKey(key));
    await reveal(tester, finder);
    await tester.tap(finder);
    await tester.pumpAndSettle();
    final main = find.byKey(const ValueKey('services-scroll'));
    if (find
            .byKey(const ValueKey('service-dialog-scroll'))
            .evaluate()
            .isEmpty &&
        main.evaluate().isNotEmpty) {
      tester
          .state<ScrollableState>(
            find.descendant(of: main, matching: find.byType(Scrollable)).first,
          )
          .position
          .jumpTo(0);
      await tester.pumpAndSettle();
    }
  }

  Future<void> confirm(WidgetTester tester) => tap(tester, 'service-confirm');
  Future<bool> enabled(WidgetTester tester, String key) async {
    await reveal(tester, find.byKey(ValueKey(key)));
    return tester
            .widget<ButtonStyleButton>(find.byKey(ValueKey(key)))
            .onPressed !=
        null;
  }

  testWidgets('unconfigured guest has honest notice and actual local export', (
    tester,
  ) async {
    final manager = NativeServicesManager();
    addTearDown(manager.dispose);
    var exported = 0;
    await show(
      tester,
      manager,
      large: true,
      export: () async {
        exported++;
        return 'local-harbor-json';
      },
    );
    await reveal(tester, find.byKey(const ValueKey('services-unconfigured')));
    expect(find.byKey(const ValueKey('services-unconfigured')), findsOneWidget);
    expect(find.byKey(const ValueKey('create-account')), findsNothing);
    expect(find.byKey(const ValueKey('enable-telemetry')), findsNothing);
    await tap(tester, 'export-local-harbor');
    expect(exported, 1);
    expect(find.text('local-harbor-json'), findsOneWidget);
    expect(find.textContaining('Nothing has been uploaded'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'creation requires cloud consent and retained code before uploads',
    (tester) async {
      final client = FixtureClient();
      final storage = MemoryCredentials();
      final manager = await managerFor(
        client,
        signedIn: false,
        storage: storage,
      );
      await show(tester, manager, large: true);
      await tap(tester, 'create-account');
      expect(await enabled(tester, 'create-account-confirm'), isFalse);
      expect(client.calls, isEmpty);
      await tap(tester, 'cloud-consent');
      await tap(tester, 'create-account-confirm');
      expect(client.calls, ['create:true']);
      expect(find.text(client.currentCode), findsOneWidget);
      expect(manager.recoveryAcknowledged, isFalse);
      expect(await enabled(tester, 'recovery-retained-confirm'), isFalse);
      await tap(tester, 'recovery-retained');
      await tap(tester, 'recovery-retained-confirm');
      expect(manager.recoveryAcknowledged, isTrue);
      expect(
        storage.values.values.any(
          (value) => value.contains('fixture-recovery-code'),
        ),
        isFalse,
      );
      expect(manager.telemetryEnabled, isFalse);
      expect(client.calls, ['create:true']);
      await tap(tester, 'refresh-cloud');
      expect(await enabled(tester, 'upload-harbor'), isTrue);
      expect(find.text('secret-session-token-not-for-ui'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'unacknowledged account stays upload locked across manager reload',
    (tester) async {
      final storage = MemoryCredentials();
      final original = await managerFor(
        FixtureClient(),
        signedIn: false,
        storage: storage,
      );
      await original.createAccount(cloudConsent: true);
      final client = FixtureClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: storage,
      );
      addTearDown(manager.dispose);
      await manager.initialize();
      expect(manager.signedIn, isTrue);
      expect(manager.recoveryAcknowledged, isFalse);
      await show(tester, manager);
      await tap(tester, 'refresh-cloud');
      expect(await enabled(tester, 'upload-harbor'), isFalse);
      expect(client.calls, ['index']);
    },
  );
  testWidgets('recovery never exports or replaces guest harbor', (
    tester,
  ) async {
    final client = FixtureClient();
    final manager = await managerFor(client, signedIn: false);
    var imports = 0, exports = 0;
    await show(
      tester,
      manager,
      large: true,
      import: (_) async => imports++,
      export: () async {
        exports++;
        return 'guest';
      },
    );
    await tap(tester, 'recover-account');
    expect(await enabled(tester, 'recover-confirm'), isFalse);
    await tester.enterText(
      find.byKey(const ValueKey('recover-account-id')),
      accountId,
    );
    await tester.enterText(
      find.byKey(const ValueKey('recover-code')),
      client.currentCode,
    );
    await tap(tester, 'recover-confirm');
    expect(manager.signedIn, isTrue);
    expect(client.calls, ['recover']);
    expect(imports, 0);
    expect(exports, 0);
    expect(
      find.textContaining('Your local harbor is unchanged'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
  testWidgets('reviewed cloud cursor CAS selects before whole-save import', (
    tester,
  ) async {
    final client = FixtureClient();
    final manager = await managerFor(client);
    final imported = <String>[];
    await show(
      tester,
      manager,
      large: true,
      import: (text) async => imported.add(text),
    );
    await tap(tester, 'refresh-cloud');
    await reveal(tester, find.text('Cloud revision 7'));
    expect(find.text('Cloud revision 7'), findsOneWidget);
    await reveal(tester, find.text('Revision 19'));
    expect(find.text('Revision 19'), findsOneWidget);
    await tap(tester, 'choose-cloud-$secondSave');
    expect(imported, isEmpty);
    expect(find.textContaining('preserved'), findsOneWidget);
    await confirm(tester);
    expect(client.calls, [
      'index',
      'download:$secondSave',
      'select:$secondSave:7:true',
      'index',
    ]);
    expect(imported, ['cloud-export-$secondSave']);
    expect(tester.takeException(), isNull);
  });
  testWidgets('CAS conflict never imports or merges', (tester) async {
    final client = FixtureClient();
    final manager = await managerFor(client);
    var imports = 0;
    await show(tester, manager, import: (_) async => imports++);
    await tap(tester, 'refresh-cloud');
    client.conflict = true;
    await tap(tester, 'choose-cloud-$firstSave');
    await confirm(tester);
    expect(imports, 0);
    expect(client.selected, isNull);
    expect(find.textContaining('Cloud data changed'), findsOneWidget);
  });
  testWidgets('upload exports after confirmation using observed generation', (
    tester,
  ) async {
    final client = FixtureClient();
    final manager = await managerFor(client);
    var exports = 0;
    await show(
      tester,
      manager,
      export: () async {
        exports++;
        return 'complete-local-save';
      },
    );
    await tap(tester, 'refresh-cloud');
    await tap(tester, 'upload-harbor');
    expect(exports, 0);
    expect(client.uploaded, isNull);
    await confirm(tester);
    expect(exports, 1);
    expect(client.uploaded, 'complete-local-save');
    expect(client.calls, contains('upload:7'));
  });
  testWidgets('failed import after cloud selection is reported honestly', (
    tester,
  ) async {
    final client = FixtureClient();
    final manager = await managerFor(client);
    await show(
      tester,
      manager,
      import: (_) async => throw const FormatException('fixture invalid save'),
    );
    await tap(tester, 'refresh-cloud');
    await tap(tester, 'choose-cloud-$firstSave');
    await confirm(tester);
    expect(client.selected, firstSave);
    expect(
      find.textContaining('local import did not confirm completion'),
      findsOneWidget,
    );
    expect(find.textContaining('fixture invalid save'), findsNothing);
  });
  testWidgets(
    'rotation retains new code before request and explains lost reply',
    (tester) async {
      final client = FixtureClient()..loseRotationReply = true;
      final manager = await managerFor(client);
      await show(tester, manager, large: true);
      await tap(tester, 'rotate-recovery');
      final newCode = tester
          .widget<SelectableText>(
            find.byKey(const ValueKey('rotation-new-code')),
          )
          .data!;
      await tester.enterText(
        find.byKey(const ValueKey('rotation-current-code')),
        client.currentCode,
      );
      expect(await enabled(tester, 'rotation-confirm'), isFalse);
      expect(client.rotatedCode, isNull);
      await tap(tester, 'rotation-retained');
      await tap(tester, 'rotation-confirm');
      expect(client.rotatedCode, newCode);
      expect(
        find.textContaining('may have completed if the reply was lost'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('network signout and offline forget report distinct outcomes', (
    tester,
  ) async {
    final client = FixtureClient()..offline = true;
    final manager = await managerFor(client);
    await show(tester, manager);
    await tap(tester, 'sign-out');
    await confirm(tester);
    expect(manager.signedIn, isTrue);
    expect(client.calls, ['revoke']);
    await tap(tester, 'forget-session');
    await confirm(tester);
    expect(manager.signedIn, isFalse);
    expect(client.calls, ['revoke']);
    expect(
      find.textContaining('Server revocation was not confirmed'),
      findsOneWidget,
    );
  });
  testWidgets('delete requires code and consent while keeping local harbor', (
    tester,
  ) async {
    final client = FixtureClient();
    final manager = await managerFor(client);
    var imports = 0, exports = 0;
    await show(
      tester,
      manager,
      large: true,
      import: (_) async => imports++,
      export: () async {
        exports++;
        return 'local';
      },
    );
    await tap(tester, 'delete-account');
    await tester.enterText(
      find.byKey(const ValueKey('delete-recovery-code')),
      client.currentCode,
    );
    expect(await enabled(tester, 'delete-account-confirm'), isFalse);
    await tap(tester, 'delete-account-consent');
    await tap(tester, 'delete-account-confirm');
    expect(client.calls, ['delete:true']);
    expect(manager.signedIn, isFalse);
    expect(imports, 0);
    expect(exports, 0);
    expect(find.textContaining('Your local harbor is kept'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'telemetry separate consent and failed deletion stop local collection',
    (tester) async {
      final client = FixtureClient();
      final manager = await managerFor(client);
      await show(tester, manager, large: true);
      await tap(tester, 'enable-telemetry');
      expect(manager.telemetryEnabled, isFalse);
      await confirm(tester);
      expect(manager.telemetryEnabled, isTrue);
      client.offline = true;
      await tap(tester, 'disable-telemetry');
      expect(manager.telemetryEnabled, isFalse);
      expect(manager.pendingTelemetryDeletion, isTrue);
      await reveal(
        tester,
        find.byKey(const ValueKey('telemetry-deletion-pending')),
      );
      expect(
        find.byKey(const ValueKey('telemetry-deletion-pending')),
        findsOneWidget,
      );
      client.offline = false;
      await tap(tester, 'retry-telemetry-delete');
      expect(manager.pendingTelemetryDeletion, isFalse);
      expect(client.remoteTelemetry, isFalse);
      expect(client.calls, [
        'telemetry:true',
        'telemetry:false',
        'telemetry:false',
      ]);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('account export shows returned data without claiming file save', (
    tester,
  ) async {
    final client = FixtureClient();
    final manager = await managerFor(client);
    await show(tester, manager);
    await tap(tester, 'export-account');
    expect(client.calls, ['export-account']);
    expect(find.textContaining('fixture-save-data'), findsOneWidget);
    expect(find.textContaining('does not save a file'), findsOneWidget);
    expect(find.textContaining('secret-session-token'), findsNothing);
  });
  testWidgets(
    'actual loopback HTTP account request follows UI consent without upload',
    (tester) async {
      HttpServer? server;
      final requests = <String>[];
      late NativeServicesManager manager;
      await tester.runAsync(() async {
        server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
        server!.listen((request) async {
          requests.add('${request.method} ${request.uri.path}');
          expect(jsonDecode(await utf8.decoder.bind(request).join()), {
            'consent_cloud': true,
          });
          request.response.headers.contentType = ContentType.json;
          request.response.write(
            jsonEncode({
              'account_id': accountId,
              'session_token': 'loopback-secret-token',
              'expires_at': DateTime.utc(2035).millisecondsSinceEpoch ~/ 1000,
              'recovery_code': 'loopback-retained-recovery',
            }),
          );
          await request.response.close();
        });
        manager = NativeServicesManager(
          client: TideglassServiceClient(
            endpoint: Uri.parse('http://127.0.0.1:${server!.port}'),
            allowLocalDevelopment: true,
            httpClient: HttpOverrides.runWithHttpOverrides(
              () => HttpClient(),
              LoopbackHttpOverrides(),
            ),
          ),
          credentials: MemoryCredentials(),
        );
        await manager.initialize();
      });
      addTearDown(() async {
        manager.dispose();
        await server?.close(force: true);
      });
      await show(tester, manager);
      await reveal(tester, find.byKey(const ValueKey('create-account')));
      await tester.runAsync(() async {
        await tester.tap(find.byKey(const ValueKey('create-account')));
      });
      await tester.pumpAndSettle();
      expect(requests, isEmpty);
      await tap(tester, 'cloud-consent');
      final create = find.byKey(const ValueKey('create-account-confirm'));
      await tester.ensureVisible(create);
      await tester.runAsync(() async {
        await tester.tap(create);
        await tester.pump();
        final deadline = DateTime.now().add(const Duration(seconds: 3));
        while (!manager.signedIn && DateTime.now().isBefore(deadline)) {
          await Future<void>.delayed(const Duration(milliseconds: 10));
        }
      });
      await tester.pumpAndSettle();
      expect(requests, ['POST /v1/accounts']);
      expect(manager.signedIn, isTrue);
      expect(find.text('loopback-retained-recovery'), findsOneWidget);
      expect(manager.recoveryAcknowledged, isFalse);
      expect(find.text('loopback-secret-token'), findsNothing);
    },
  );
}
