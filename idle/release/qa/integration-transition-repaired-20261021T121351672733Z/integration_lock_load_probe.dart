import 'dart:io';
import 'package:tideglass_persistence/tideglass_persistence.dart';
Future<void> main(List<String> args) async {
 final r=SaveRepository(Directory(args.single),economicVersion:'tideglass-economy-1.0.0',economicDigest:'9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6',validatePayload:(_){ });
 try {await r.load();stdout.writeln('LOADED');}catch(e){stdout.writeln('${e.runtimeType}: $e');}
}
