import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:test/test.dart';
import 'package:tideglass_platform/soundtrack_delivery.dart';
import 'package:tideglass_platform/tideglass_platform.dart';

void main() {
  late HttpServer server;
  late TideglassServiceClient client;
  late SoundtrackDelivery delivery;
  late Directory folder;
  final bytes = List<int>.generate(131072, (i) => i % 251);
  final hash = sha256.convert(bytes).toString();
  var mode = 'ok';
  final requests = <String>[];
  Completer<void>? bodyGate, bodyStarted;
  setUp(() async {
    mode = 'ok';
    requests.clear();
    bodyGate = null;
    bodyStarted = null;
    server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    folder = await Directory.systemTemp.createTemp('tideglass-download-test-');
    client =
        TideglassServiceClient(
            endpoint: Uri.parse('http://127.0.0.1:${server.port}'),
            allowLocalDevelopment: true,
          )
          ..session = ServiceSession(
            accountId: 'fixture-account',
            token: 'private-test-token',
            expiresAt: DateTime.utc(2035),
          );
    delivery = SoundtrackDelivery(client);
    server.listen((request) async {
      try {
        requests.add(request.uri.toString());
        expect(request.uri.hasQuery, isFalse);
        expect(
          request.headers.value(HttpHeaders.authorizationHeader),
          'Bearer private-test-token',
        );
        if (request.uri.path == '/v1/commerce/capabilities') {
          if (mode == 'drip') {
            request.response.write('{');
            await request.response.flush();
            await Future<void>.delayed(const Duration(milliseconds: 200));
            request.response.write('}');
            await request.response.close();
            return;
          }
          request.response.write(
            jsonEncode({'soundtrack_delivery_ready': mode != 'unconfigured'}),
          );
        } else if (request.uri.path == '/v1/soundtrack/manifest') {
          if (mode == 'denied') {
            request.response.statusCode = 403;
          } else {
            request.response.write(
              jsonEncode({
                'asset_id': 'soundtrack.01',
                'filename': SoundtrackDelivery.filename,
                'content_type': 'application/zip',
                'bytes': mode == 'oversized'
                    ? SoundtrackDelivery.maximumBytes + 1
                    : bytes.length,
                'sha256': hash,
                'download_path': mode == 'foreign_path'
                    ? 'https://example.invalid/collect'
                    : '/v1/soundtrack/download',
              }),
            );
          }
        } else if (request.uri.path == '/v1/soundtrack/download') {
          if (mode == 'redirect') {
            request.response.statusCode = 302;
            request.response.headers.set(
              HttpHeaders.locationHeader,
              '/should-not-follow',
            );
          } else {
            request.response.headers.contentType = ContentType(
              'application',
              'zip',
            );
            request.response.headers.set('X-Content-SHA256', hash);
            request.response.contentLength = bytes.length;
            bodyStarted?.complete();
            await bodyGate?.future;
            if (mode == 'cleanup_failure') {
              final staging = (await folder.list().toList()).single;
              final chmod = await Process.run('chmod', ['500', staging.path]);
              expect(chmod.exitCode, 0);
            }
            request.response.add(
              mode == 'corrupt' || mode == 'cleanup_failure'
                  ? List.filled(bytes.length, 0)
                  : bytes,
            );
          }
        } else {
          fail('Unexpected endpoint ${request.uri.path}');
        }
        await request.response.close();
      } on SocketException {
        // A captured session can be invalidated while this fixture is streaming.
      } on HttpException {
        // The client intentionally aborts rejected responses.
      }
    });
  });
  tearDown(() async {
    client.close();
    await server.close(force: true);
    if (!Platform.isWindows) {
      await Process.run('chmod', ['-R', 'u+rwX', folder.path]);
    }
    await folder.delete(recursive: true);
  });

  test(
    'authenticated bytes are verified and published without credential URLs',
    () async {
      expect(await delivery.ready(), isTrue);
      final file = await delivery.download(folder);
      expect(await file.readAsBytes(), bytes);
      expect(file.uri.pathSegments.last, SoundtrackDelivery.filename);
      expect(
        await folder.list(recursive: true).any((f) => f.path.endsWith('.part')),
        isFalse,
      );
      expect(requests, [
        '/v1/commerce/capabilities',
        '/v1/soundtrack/manifest',
        '/v1/soundtrack/download',
      ]);
    },
  );

  for (final fixture in [
    'foreign_path',
    'oversized',
    'denied',
    'redirect',
    'corrupt',
  ]) {
    test('$fixture fails closed and removes incomplete files', () async {
      mode = fixture;
      await expectLater(
        delivery.download(folder),
        throwsA(isA<ServiceException>()),
      );
      expect(await folder.list().toList(), isEmpty);
      expect(requests, isNot(contains('/should-not-follow')));
      if (fixture == 'foreign_path' ||
          fixture == 'oversized' ||
          fixture == 'denied') {
        expect(requests, ['/v1/soundtrack/manifest']);
      }
    });
  }

  test(
    'account replacement during transfer cannot publish to the new session',
    () async {
      bodyGate = Completer<void>();
      bodyStarted = Completer<void>();
      final result = delivery.download(folder);
      await bodyStarted!.future;
      client.session = ServiceSession(
        accountId: 'replacement-account',
        token: 'new-test-token',
        expiresAt: DateTime.utc(2035),
      );
      bodyGate!.complete();
      await expectLater(result, throwsA(isA<ServiceException>()));
      expect(await folder.list().toList(), isEmpty);
    },
  );

  test('guest and unavailable fulfillment cannot claim readiness', () async {
    mode = 'unconfigured';
    expect(await delivery.ready(), isFalse);
    client.session = null;
    expect(await delivery.ready(), isFalse);
    await expectLater(
      delivery.download(folder),
      throwsA(isA<ServiceException>()),
    );
    expect(requests, ['/v1/commerce/capabilities']);
  });
  test(
    'absolute JSON deadline bounds a response that starts but drips',
    () async {
      mode = 'drip';
      delivery = SoundtrackDelivery(
        client,
        jsonDeadline: const Duration(milliseconds: 50),
      );
      final watch = Stopwatch()..start();
      await expectLater(delivery.ready(), throwsA(isA<ServiceException>()));
      expect(watch.elapsed, lessThan(const Duration(seconds: 1)));
      await Future<void>.delayed(const Duration(milliseconds: 250));
    },
  );
  test(
    'cleanup permission failure is normalized and does not lock future downloads',
    () async {
      mode = 'cleanup_failure';
      await expectLater(
        delivery.download(folder),
        throwsA(
          isA<ServiceException>().having(
            (e) => e.code,
            'code',
            'soundtrack_cleanup_failed',
          ),
        ),
      );
      await Process.run('chmod', ['-R', 'u+rwX', folder.path]);
      mode = 'ok';
      final file = await delivery.download(folder);
      expect(await file.readAsBytes(), bytes);
    },
    skip: Platform.isWindows,
  );
}
