import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:tideglass_platform/soundtrack_delivery.dart';
import 'package:tideglass_platform/tideglass_platform.dart';
Future<void> main(List<String> args) async {
  final input = jsonDecode(await File(args.single).readAsString()) as Map;
  final client = TideglassServiceClient(endpoint: Uri.parse(input['origin'] as String), allowLocalDevelopment: true)
    ..session = ServiceSession(accountId: input['account'] as String,
      token: input['token'] as String, expiresAt: DateTime.utc(2035));
  final destination = Directory(input['destination'] as String);
  try {
    final delivery = SoundtrackDelivery(client);
    if (!await delivery.ready()) throw StateError('Actual backend not ready');
    final file = await delivery.download(destination);
    final digest = await sha256.bind(file.openRead()).first;
    final length = await file.length();
    if (length != 52699186 || digest.toString() != '620d671ae8817239f89802a9bead7cb584f1e44326aedd4d352ec69fb1f8de3a') {
      throw StateError('Actual archive did not match pinned release artifact');
    }
    print(jsonEncode({'status': 'passed', 'bytes': length, 'sha256': '$digest',
      'filename': file.uri.pathSegments.last, 'actual_backend_http_and_dart_client': true,
      'ownership_source': 'explicit fixture purchase row, not a real store transaction'}));
  } finally { client.close(); }
}
