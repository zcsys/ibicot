import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

void main() {
  test('HTTPS is required except explicit loopback development', () {
    for (final uri in [
      'http://example.com',
      'http://127.0.0.1',
      'https://user:secret@example.com',
      'https://example.com/path',
      'https://example.com?token=x',
    ]) {
      expect(
        () => TideglassServiceClient(endpoint: Uri.parse(uri)),
        throwsArgumentError,
      );
    }
    final client = TideglassServiceClient(
      endpoint: Uri.parse('http://127.0.0.1:8765'),
      allowLocalDevelopment: true,
    );
    client.close();
  });
  test('missing opt-in session never contacts transport', () async {
    final client = TideglassServiceClient(
      endpoint: Uri.parse('https://example.invalid'),
    );
    await expectLater(
      client.cloudIndex(),
      throwsA(
        isA<ServiceException>().having(
          (e) => e.code,
          'code',
          'authentication_required',
        ),
      ),
    );
    client.close();
  });
  test('real service account lifecycle and fail-closed ownership', () async {
    final root = Directory.current.parent.parent.path;
    final dir = await Directory.systemTemp.createTemp(
      'tideglass-service-client-',
    );
    final process = await Process.start('python3', [
      '-m',
      'services.tideglass_service',
      '--database',
      '${dir.path}/service.sqlite3',
      '--port',
      '0',
    ], workingDirectory: root);
    final line = await process.stdout
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .first
        .timeout(const Duration(seconds: 15));
    final port = RegExp(r'127.0.0.1:(\d+)').firstMatch(line)!.group(1)!;
    final endpoint = Uri.parse('http://127.0.0.1:$port');
    final client = TideglassServiceClient(
      endpoint: endpoint,
      allowLocalDevelopment: true,
    );
    final second = TideglassServiceClient(
      endpoint: endpoint,
      allowLocalDevelopment: true,
    );
    try {
      final created = await client.createAccount(cloudConsent: true);
      expect(created.toString(), isNot(contains(created.recoveryCode)));
      expect(
        created.session.toString(),
        isNot(contains(created.session.token)),
      );
      expect((await client.cloudIndex()).snapshots, isEmpty);
      final local = SaveRepository(
        Directory('${dir.path}/device-a'),
        economicVersion: 'tideglass-economy-1.0.0',
        economicDigest: 'a' * 64,
        validatePayload: (_) {},
      );
      await local.load();
      final payload = {
        'core': {
          'wallet_micros': '15000000',
          'daily': {'account_seed': 'local.seed', 'utc_offset_minutes': 0},
        },
        'caption': 'Harbor 🐟',
      };
      final original = await local.save(
        payload,
        settledThrough: DateTime.utc(2026, 10, 16),
      );
      final firstExport = await local.exportSave();
      final uploaded = await client.uploadSnapshot(
        firstExport,
        expectedGeneration: 0,
      );
      expect(uploaded.selectedSaveId, original.saveId);
      expect(uploaded.generation, 1);
      expect(await client.downloadSnapshot(original.saveId), firstExport);
      // A second repository retains its guest branch before explicit recovery.
      final other = SaveRepository(
        Directory('${dir.path}/device-b'),
        economicVersion: 'tideglass-economy-1.0.0',
        economicDigest: 'a' * 64,
        validatePayload: (_) {},
      );
      await other.load();
      await other.save({
        'core': {'wallet_micros': '33000000'},
      }, settledThrough: DateTime.utc(2026, 10, 16));
      final imported = await other.importSave(firstExport);
      expect(imported.payload['core']['wallet_micros'], '15000000');
      expect(await Directory('${dir.path}/device-b/recovery').list().length, 1);
      final forkUpload = await client.uploadSnapshot(
        await other.exportSave(),
        expectedGeneration: 1,
      );
      expect(forkUpload.selectionRequired, isTrue);
      expect(forkUpload.selectedSaveId, original.saveId);
      final selection = await client.selectSnapshot(
        imported.saveId,
        expectedGeneration: 1,
        confirmSelection: true,
      );
      expect(selection.selectedSaveId, imported.saveId);
      expect(
        (await local.load()).snapshot!.payload['core']['wallet_micros'],
        '15000000',
      );

      await second.recoverAccount(
        accountId: created.session.accountId,
        recoveryCode: created.recoveryCode,
      );
      expect(
        (await second.exportAccount())['account']['id'],
        created.session.accountId,
      );
      final reader = ServicePassEntitlementReader(
        client,
        localAccountId: 'local.seed',
      );
      expect(
        await reader.read(accountId: 'local.seed', passId: 'pass.01'),
        isNull,
      );
      await expectLater(
        client.verifyPurchase(
          platform: 'apple',
          proof: 'unverified-client-claim',
        ),
        throwsA(
          isA<ServiceException>().having(
            (e) => e.code,
            'code',
            'verification_unavailable',
          ),
        ),
      );
      expect(await client.setTelemetryConsent(true), 1);
      expect(await client.setTelemetryConsent(false), 2);
      final rotated = await client.rotateRecoveryCode(
        created.recoveryCode,
        newRecoveryCode: TideglassServiceClient.generateRecoveryCode(),
      );
      await expectLater(
        second.cloudIndex(),
        throwsA(isA<ServiceException>().having((e) => e.status, 'status', 401)),
      );
      await client.deleteAccount(
        recoveryCode: rotated.recoveryCode,
        confirmDelete: true,
      );
      expect(client.session, isNull);
    } finally {
      client.close();
      second.close();
      process.kill();
      await process.exitCode;
      await dir.delete(recursive: true);
    }
  });
  test(
    'redirect cannot forward bearer credentials to another endpoint',
    () async {
      final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      var hits = 0;
      server.listen((request) async {
        hits++;
        request.response.statusCode = 302;
        request.response.headers.set(HttpHeaders.locationHeader, '/captured');
        request.response.write('{"error":"redirect_rejected"}');
        await request.response.close();
      });
      final client = TideglassServiceClient(
        endpoint: Uri.parse('http://127.0.0.1:${server.port}'),
        allowLocalDevelopment: true,
      );
      client.session = ServiceSession(
        accountId: 'unused',
        token: 'sensitive',
        expiresAt: DateTime.now().add(const Duration(days: 1)),
      );
      try {
        await expectLater(
          client.cloudIndex(),
          throwsA(
            isA<ServiceException>().having((e) => e.status, 'status', 302),
          ),
        );
        expect(hits, 1);
      } finally {
        client.close();
        await server.close(force: true);
      }
    },
  );
}
