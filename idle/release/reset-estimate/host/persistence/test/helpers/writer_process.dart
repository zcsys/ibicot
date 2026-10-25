import 'dart:io';
import 'dart:isolate';
import 'package:tideglass_persistence/tideglass_persistence.dart';

Future<void> main(List<String> args) async {
  final store = SaveRepository(
    Directory(args[0]),
    economicVersion: 'tideglass-economy-1.0.0',
    economicDigest:
        '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6',
    validatePayload: (value) {
      if (value['amount'] is! int) throw const FormatException('amount');
    },
    commitProbe: (stage) async {
      if (stage.name == args[1]) {
        stdout.writeln('LOCKED');
        await stdout.flush();
        // A bare unresolved Future does not keep the Dart VM alive.
        final keepAlive = ReceivePort();
        await keepAlive.first;
        keepAlive.close();
      }
    },
  );
  await store.load();
  await store.save({'amount': 1}, settledThrough: DateTime.utc(2026, 10, 21));
}
