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
  final bytes = List<int>.generate(8192, (i) => (i * 17) % 256);
  final digest = sha256.convert(bytes).toString();
  var wrong = '', downloads = 0;
  Completer<void>? manifestGate, manifestEntered, bodyGate, bodyEntered;
  setUp(() async {
    server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    folder = await Directory.systemTemp.createTemp('tideglass-qa-stream-');
    client = TideglassServiceClient(endpoint: Uri.parse('http://127.0.0.1:${server.port}'), allowLocalDevelopment: true)
      ..session = ServiceSession(accountId: 'qa-account', token: 'qa-local-token', expiresAt: DateTime.utc(2035));
    delivery = SoundtrackDelivery(client); wrong = ''; downloads = 0;
    manifestGate = null; manifestEntered = null; bodyGate = null; bodyEntered = null;
    server.listen((request) async {
      try {
        expect(request.uri.hasQuery, isFalse);
        expect(request.headers.value(HttpHeaders.authorizationHeader), 'Bearer qa-local-token');
        if (request.uri.path == '/v1/soundtrack/manifest') {
          if (manifestEntered != null && !manifestEntered!.isCompleted) manifestEntered!.complete();
          await manifestGate?.future;
          request.response.write(jsonEncode({'asset_id': 'soundtrack.01', 'filename': SoundtrackDelivery.filename,
            'content_type': 'application/zip', 'bytes': bytes.length, 'sha256': digest,
            'download_path': '/v1/soundtrack/download'}));
        } else if (request.uri.path == '/v1/soundtrack/download') {
          downloads++;
          request.response.headers.contentType = ContentType('application', wrong == 'mime' ? 'octet-stream' : 'zip');
          request.response.headers.set('X-Content-SHA256', wrong == 'hash' ? '0' * 64 : digest);
          request.response.contentLength = wrong == 'length' ? bytes.length + 1 : bytes.length;
          if (bodyEntered != null && !bodyEntered!.isCompleted) bodyEntered!.complete();
          await bodyGate?.future; request.response.add(bytes);
          if (wrong == 'length') request.response.add([0]);
        } else { fail('Unexpected route'); }
        await request.response.close();
      } on SocketException { /* Intentional client denial aborts the fixture. */ }
        on HttpException { /* Intentional client denial aborts the fixture. */ }
    });
  });
  tearDown(() async { client.close(); await server.close(force: true); await folder.delete(recursive: true); });
  test('same session object restored after signout cannot complete an old manifest', () async {
    manifestGate = Completer<void>(); manifestEntered = Completer<void>();
    final pending = delivery.download(folder); await manifestEntered!.future;
    final original = client.session; client.session = null; client.session = original;
    manifestGate!.complete();
    await expectLater(pending, throwsA(isA<ServiceException>()));
    expect(downloads, 0); expect(await folder.list().toList(), isEmpty);
  });
  test('session expiry during actual HTTP body transfer erases partial export', () async {
    client.session = ServiceSession(accountId: 'qa-account', token: 'qa-local-token',
      expiresAt: DateTime.now().toUtc().add(const Duration(milliseconds: 300)));
    bodyGate = Completer<void>(); bodyEntered = Completer<void>();
    final pending = delivery.download(folder); await bodyEntered!.future;
    await Future<void>.delayed(const Duration(milliseconds: 350)); bodyGate!.complete();
    await expectLater(pending, throwsA(isA<ServiceException>())); expect(await folder.list().toList(), isEmpty);
  });
  test('concurrent export rejects without interfering with valid transfer or next retry', () async {
    manifestGate = Completer<void>(); manifestEntered = Completer<void>();
    final first = delivery.download(folder); await manifestEntered!.future;
    await expectLater(delivery.download(folder), throwsA(isA<ServiceException>().having((e) => e.code, 'code', 'soundtrack_download_in_progress')));
    manifestGate!.complete(); final file = await first; expect(await file.readAsBytes(), bytes);
    manifestGate = null; final second = await delivery.download(folder);
    expect(await second.readAsBytes(), bytes); expect(downloads, 2);
  });
  for (final header in ['mime', 'hash', 'length']) {
    test('incorrect $header response header fails before publication', () async {
      wrong = header; await expectLater(delivery.download(folder), throwsA(isA<ServiceException>()));
      expect(await folder.list().toList(), isEmpty);
    });
  }
}
